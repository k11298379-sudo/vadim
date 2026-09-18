import os
import sys

# Ensure root directory is always in sys.path regardless of how main.py is called
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure console supports UTF-8 emojis without crashing on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import settings
from backend.db.session import init_db, async_session_factory
from backend.db.seed import seed_initial_data
from backend.api.routes import api_router
from backend.bot.bot import create_bot_and_dispatcher
from backend.bot.services.scheduler import setup_scheduler

# Configure logging with console and file handler
from logging.handlers import RotatingFileHandler
os.makedirs("data", exist_ok=True)
_file_handler = RotatingFileHandler(
    os.path.join("data", "bot.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        _file_handler
    ]
)
logger = logging.getLogger("botdz")

bot, dp = create_bot_and_dispatcher()
polling_task: asyncio.Task | None = None

from backend.bot.services.commands import setup_bot_commands

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Initializing database...")
    await init_db()

    async with async_session_factory() as session:
        await seed_initial_data(session)
        from backend.db.crud.homework import cleanup_past_homework_statuses
        cleaned = await cleanup_past_homework_statuses(session)
        if cleaned > 0:
            logger.info(f"Startup checklist cleanup: deleted {cleaned} obsolete records from past homework.")

        # Clean up any obsolete schedules on or before 2026-09-01
        from datetime import date
        from sqlalchemy import delete
        from backend.db.models import Schedule
        res_del = await session.execute(
            delete(Schedule).where(Schedule.specific_date <= date(2026, 9, 1))
        )
        if res_del.rowcount and res_del.rowcount > 0:
            await session.commit()
            logger.info(f"Purged {res_del.rowcount} obsolete schedule records on or before 2026-09-01.")

    logger.info("Setting up background scheduler...")
    setup_scheduler(bot)

    # Check duty notification on startup
    from backend.bot.services.notifier import check_and_send_duty_reminder
    asyncio.create_task(check_and_send_duty_reminder(bot))

    # Catch-up evening digest on startup if 19:00 has already passed today
    async def check_and_send_evening_digest_on_startup():
        try:
            await asyncio.sleep(3)
            from backend.config import get_current_date_and_hour
            today, current_hour = get_current_date_and_hour()
            if today.isoweekday() in (5, 6):
                # По пятницам и субботам вечером уведомления не отправляются
                return
            if current_hour >= 19:
                from backend.db.crud import get_class_setting, set_class_setting
                async with async_session_factory() as session:
                    last_sent = await get_class_setting(session, "last_evening_digest_date")
                    if last_sent != str(today):
                        logger.info(f"Startup: 19:00 passed and evening digest not yet sent for {today}. Sending now...")
                        await set_class_setting(session, "last_evening_digest_date", str(today))
                        from backend.bot.services.notifier import send_evening_digest
                        await send_evening_digest(bot)
                        logger.info(f"Startup: evening digest for {today} sent successfully.")
        except Exception as ex:
            logger.warning(f"Error checking evening digest on startup: {ex}")

    asyncio.create_task(check_and_send_evening_digest_on_startup())

    # Catch-up birthday greetings on startup if not yet checked/sent today
    async def check_and_send_birthdays_on_startup():
        try:
            await asyncio.sleep(4)
            from backend.bot.services.birthdays import check_and_send_birthday_greetings
            await check_and_send_birthday_greetings(bot)
        except Exception as ex:
            logger.warning(f"Error checking birthday greetings on startup: {ex}")

    asyncio.create_task(check_and_send_birthdays_on_startup())

    # Start HTTPS Tunnel in background once uvicorn server is listening
    port = int(os.environ.get("PORT", settings.PORT))
    if getattr(settings, "AUTO_TUNNEL", True) and not settings.WEBAPP_URL.startswith("https://"):
        async def _init_tunnel():
            await asyncio.sleep(1.0)
            try:
                from backend.tunnel import start_tunnel, register_url_change_callback

                async def _on_tunnel_update(new_url: str):
                    settings.WEBAPP_URL = f"{new_url}/app"
                    settings.BASE_URL = new_url
                    logger.info(f"Dynamic tunnel updated: {settings.WEBAPP_URL}")
                    try:
                        await setup_bot_commands(bot)
                    except Exception as ex:
                        logger.warning(f"Could not reconfigure bot commands on tunnel change: {ex}")

                register_url_change_callback(_on_tunnel_update)

                tunnel_url = await start_tunnel(port)
                if tunnel_url:
                    settings.WEBAPP_URL = f"{tunnel_url}/app"
                    settings.BASE_URL = tunnel_url
                    print("\n" + "=" * 64)
                    print(f"🚀 ПУБЛИЧНЫЙ HTTPS ТУННЕЛЬ АКТИВЕН!")
                    print(f"📱 Ссылка на Mini App: {settings.WEBAPP_URL}")
                    print("=" * 64 + "\n", flush=True)
                    try:
                        await setup_bot_commands(bot)
                    except Exception as ex:
                        logger.warning(f"Could not update bot commands on initial tunnel start: {ex}")
            except Exception as e:
                logger.warning(f"Could not start tunnel: {e}")

        asyncio.create_task(_init_tunnel())

    # Start Aiogram polling and register command hints in background task
    global polling_task
    if settings.ENABLE_BOT_POLLING and settings.BOT_TOKEN and not settings.BOT_TOKEN.startswith("1234567890:ABCdef"):
        async def init_telegram_bot():
            try:
                logger.info("Registering Telegram command autocomplete hints and menu button...")
                await asyncio.wait_for(setup_bot_commands(bot), timeout=5.0)
            except Exception as e:
                logger.warning(f"Could not setup Telegram commands (offline or timeout): {e}")
            logger.info("Starting Telegram Bot long-polling...")
            while True:
                try:
                    await dp.start_polling(bot, handle_signals=False)
                    break
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Telegram polling error (retrying in 5s): {e}")
                    await asyncio.sleep(5)

        polling_task = asyncio.create_task(init_telegram_bot())

        # Send deploy completion notification to admin
        if settings.ADMIN_ID:
            async def send_startup_alert():
                try:
                    await asyncio.sleep(1)
                    from backend.config import get_today
                    today_str = get_today().strftime("%d.%m.%Y")
                    is_dev_db = "sqlite" in settings.DATABASE_URL
                    bot_header = (
                        "🧪 **Тестовый бот (Dev) успешно запущен на localhost!**"
                        if is_dev_db
                        else "🚀 **Деплой успешно завершен! Бот 11 «Б» запущен.**"
                    )
                    db_name = "SQLite (Локальная база dev)" if is_dev_db else "Neon PostgreSQL"
                    webapp_info = (
                        f"📱 **Mini App для телефона:**\n{settings.WEBAPP_URL}\n"
                        if settings.WEBAPP_URL.startswith("https://")
                        else ""
                    )
                    extra_info = (
                        f"🌐 Порт: `{settings.PORT}`\n🔔 Все модули и Mini App готовы к тестам!"
                        if is_dev_db
                        else f"🌐 Порт: `{settings.PORT}`\n🔔 Все модули, расписание, звонки и Mini App готовы к работе!"
                    )
                    await bot.send_message(
                        chat_id=settings.ADMIN_ID,
                        text=(
                            f"{bot_header}\n\n"
                            f"📅 **Дата:** `{today_str}`\n"
                            f"⚡ База данных: `{db_name}`\n"
                            f"{extra_info}\n"
                            f"{webapp_info}"
                        ),
                        parse_mode="Markdown"
                    )
                    logger.info("Deploy notification successfully sent to admin.")
                except Exception as ex:
                    logger.warning(f"Could not send startup alert to admin: {ex}")

            asyncio.create_task(send_startup_alert())
    else:
        logger.warning("BOT_TOKEN is not configured or is a placeholder! Telegram bot polling will not start.")

    yield

    # --- Shutdown ---
    logger.info("Shutting down...")
    try:
        from backend.tunnel import stop_tunnel
        await stop_tunnel()
    except Exception:
        pass
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    if bot.session:
        await bot.session.close()

app = FastAPI(
    title="Class Bot & Mini App API",
    description="Backend for School / Class Telegram Bot & WebApp",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Healthcheck for Cloudflare Worker & Render
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "class-bot"}

@app.get("/favicon.ico")
async def favicon():
    return Response(content=b"", media_type="image/x-icon")


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response

# Static files for Telegram Mini App
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", NoCacheStaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/app")

@app.get("/app")
async def serve_webapp():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "Frontend not found"}

@app.get("/app/natbirzha")
async def serve_natbirzha():
    nat_index = os.path.join(frontend_path, "natbirzha", "index.html")
    if os.path.exists(nat_index):
        return FileResponse(
            nat_index,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "Natbirzha frontend not found"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run(
        app,
        host=settings.HOST,
        port=port,
        log_level="info"
    )

