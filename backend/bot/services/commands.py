import logging
from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    MenuButtonDefault,
    MenuButtonWebApp,
    WebAppInfo
)
from backend.config import settings

logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):
    """
    Настраивает команды бота и кнопку открытия Mini App в интерфейсе Telegram.
    """
    try:
        commands = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="now", description="⏳ Какой сейчас урок?"),
            BotCommand(command="fact", description="💡 Интересный факт"),
        ]
        await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllGroupChats())
        await bot.set_my_commands(commands=commands)

        if settings.WEBAPP_URL and settings.WEBAPP_URL.startswith("https://"):
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="📱 Mini App",
                    web_app=WebAppInfo(url=settings.WEBAPP_URL)
                )
            )
            logger.info(f"Telegram Menu Button configured with WebApp URL: {settings.WEBAPP_URL}")
        else:
            await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
            logger.info("Bot commands updated: /start and /fact (💡 Интересный факт) registered.")
    except Exception as e:
        logger.warning(f"Error configuring bot commands: {e}")

