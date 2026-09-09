import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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


    # Start Aiogram polling and register command hints in background task
    global polling_task
    if settings.BOT_TOKEN and not settings.BOT_TOKEN.startswith("1234567890:ABCdef"):
        logger.info("Registering Telegram command autocomplete hints...")
        await setup_bot_commands(bot)
        logger.info("Starting Telegram Bot long-polling...")
        polling_task = asyncio.create_task(dp.start_polling(bot))

        # Send deploy completion notification to admin
        if settings.ADMIN_ID:
            async def send_startup_alert():
                try:
                    await asyncio.sleep(1)
                    from backend.config import get_today
                    today_str = get_today().strftime("%d.%m.%Y")
                    db_name = "SQLite (Локальная база dev)" if "sqlite" in settings.DATABASE_URL else "Neon PostgreSQL"
                    await bot.send_message(
                        chat_id=settings.ADMIN_ID,
                        text=(
                            "🧪 **Тестовый бот (Dev) успешно запущен на localhost!**\n\n"
                            f"📅 **Дата:** `{today_str}`\n"
                            f"⚡ База данных: `{db_name}`\n"
                            f"🌐 Порт: `{settings.PORT}` (Cloudflare Worker active)\n"
                            "🔔 Все модули и Mini App готовы к тестам!"
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run(
        app,
        host=settings.HOST,
        port=port,
        log_level="info"
    )

