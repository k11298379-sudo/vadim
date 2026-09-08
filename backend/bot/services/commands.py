import logging
from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    MenuButtonDefault
)

logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):

    """
    Удаляет все слеш-команды кроме /start во всех чатах (ЛС и группах).
    Основное управление ботом осуществляется через инлайн и реплай-кнопки.
    """
    try:
        commands = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="fact", description="💡 Интересный факт")
        ]
        await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllGroupChats())
        await bot.set_my_commands(commands=commands)

        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
        logger.info("Bot commands updated: /start and /fact (💡 Интересный факт) registered.")
    except Exception as e:
        logger.warning(f"Error configuring bot commands: {e}")

