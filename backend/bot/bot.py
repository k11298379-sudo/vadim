from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from backend.config import settings
from backend.bot.middlewares.auth import AuthMiddleware
from backend.bot.handlers import start, schedule, homework, settings as bot_settings, admin, group, facts

_current_bot: Bot | None = None

def get_current_bot() -> Bot | None:
    return _current_bot

def set_current_bot(bot: Bot | None) -> None:
    global _current_bot
    _current_bot = bot

def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    global _current_bot
    token = settings.BOT_TOKEN if (settings.BOT_TOKEN and ":" in settings.BOT_TOKEN) else "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    _current_bot = bot

    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares on specific event types
    auth_middleware = AuthMiddleware()
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)
    dp.my_chat_member.middleware(auth_middleware)

    # Register Routers safely
    routers = [
        start.router,
        group.router,
        schedule.router,
        homework.router,
        facts.router,
        bot_settings.router,
        admin.router
    ]
    for r in routers:
        if r.parent_router is None:
            dp.include_router(r)

    return bot, dp
