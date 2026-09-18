from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from backend.config import settings
from backend.bot.middlewares.auth import AuthMiddleware
from backend.bot.handlers import start, schedule, homework, settings as bot_settings, admin, group, facts, economy, birthdays, polls, now

_current_bot: Bot | None = None

def get_current_bot() -> Bot | None:
    return _current_bot

def set_current_bot(bot: Bot | None) -> None:
    global _current_bot
    _current_bot = bot

def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    global _current_bot
    token = settings.BOT_TOKEN if (settings.BOT_TOKEN and ":" in settings.BOT_TOKEN) else "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    
    session = None
    if settings.TELEGRAM_PROXY:
        try:
            session = AiohttpSession(proxy=settings.TELEGRAM_PROXY)
        except Exception:
            session = None
    elif settings.TELEGRAM_API_SERVER:
        server = TelegramAPIServer.from_base(settings.TELEGRAM_API_SERVER.rstrip("/"))
        session = AiohttpSession(api=server)

    bot = Bot(
        token=token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    _current_bot = bot

    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares on specific event types (outer_middleware ensures ALL updates including unhandled text messages are processed)
    auth_middleware = AuthMiddleware()
    dp.message.outer_middleware(auth_middleware)
    dp.callback_query.outer_middleware(auth_middleware)
    dp.my_chat_member.outer_middleware(auth_middleware)

    # Register Routers safely
    routers = [
        start.router,
        group.router,
        schedule.router,
        homework.router,
        facts.router,
        birthdays.router,
        polls.router,
        now.router,
        bot_settings.router,
        economy.router,
        admin.router,
    ]
    for r in routers:
        if r.parent_router is None:
            dp.include_router(r)

    return bot, dp
