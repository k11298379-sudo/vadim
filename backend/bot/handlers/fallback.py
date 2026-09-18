"""
fallback.py — Обработчик произвольных текстовых сообщений и запросов на естественном языке.
Регистрируется последним в диспетчере, чтобы ни одно сообщение пользователя не оставалось без ответа.
"""
from typing import Optional
from aiogram import Router, Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User
from backend.bot.keyboards.main_menu import get_main_keyboard
from backend.bot.handlers.schedule import show_schedule_menu, show_bells, show_duty_roster, show_summer_countdown
from backend.bot.handlers.homework import show_homework_menu
from backend.bot.handlers.now import cmd_now
from backend.bot.handlers.facts import show_daily_fact
from backend.bot.handlers.birthdays import cmd_birthdays
from backend.bot.handlers.admin.helpers import is_admin

router = Router(name="fallback_router")


@router.message()
async def handle_any_text_message(
    message: Message,
    db_session: AsyncSession,
    current_user: Optional[User] = None,
    bot: Optional[Bot] = None
):
    """
    Обрабатывает любые текстовые сообщения, не пойманные специализированными фильтрами:
    1. Распознает распространенные ключевые слова (расписание, дз, звонки, дежурство, сейчас и т.д.).
    2. В ЛС отвечает приветствием с быстрым меню и подсказками по командам.
    3. В групповых чатах отвечает, только если к боту обратились напрямую (упоминание или ответ).
    """
    text = (message.text or message.caption or "").strip()
    clean = text.lower().replace("ё", "е")

    # В групповых чатах не отвечаем на случайные сообщения одноклассников
    if message.chat.type in ("group", "supergroup"):
        bot_inst = bot or message.bot
        is_reply_to_bot = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and bot_inst
            and message.reply_to_message.from_user.id == bot_inst.id
        )
        is_mentioned = False
        if bot_inst:
            try:
                me = await bot_inst.get_me()
                if me.username and f"@{me.username.lower()}" in clean:
                    is_mentioned = True
            except Exception:
                pass

        if not is_reply_to_bot and not is_mentioned:
            return

    # 1. Поиск по ключевым словам
    # Расписание
    if any(k in clean for k in ("расписание", "уроки", "пары", "какие уроки")):
        await show_schedule_menu(message, db_session, current_user)
        return

    # Домашка / ДЗ
    if any(k in clean for k in ("дз", "домашка", "домашнее задание", "домашняя", "что задали", "задания")):
        await show_homework_menu(message, db_session, current_user)
        return

    # Звонки
    if any(k in clean for k in ("звонки", "звонок", "перемена", "перемены")):
        await show_bells(message, db_session)
        return

    # Дежурство
    if any(k in clean for k in ("дежур", "кто дежурит", "дежурные", "дежурный", "график")):
        await show_duty_roster(message, db_session)
        return

    # Какой сейчас урок
    if any(k in clean for k in ("сейчас", "какой урок", "сколько до звонка", "идет урок")):
        await cmd_now(message, db_session)
        return

    # Дни рождения
    if any(k in clean for k in ("др", "день рождения", "дни рождения", "именинник")):
        await cmd_birthdays(message)
        return

    # Факты
    if any(k in clean for k in ("факт", "факты", "интересн")):
        await show_daily_fact(message, db_session)
        return

    # До лета осталось
    if any(k in clean for k in ("лето", "каникул", "до лета")):
        await show_summer_countdown(message)
        return

    # 2. Общий дружелюбный ответ с меню
    is_adm = is_admin(current_user, message.from_user.id) if current_user else False
    user_name = current_user.display_name if current_user else (message.from_user.first_name or "Ученик")

    help_text = (
        f"👋 **{user_name}, я бот 11 «Б» класса!**\n\n"
        "Я умею отвечать на текстовые запросы и показывать всю информацию по классу:\n\n"
        "📅 **«расписание»** — уроки на сегодня и любой день\n"
        "📚 **«дз»** — домашние задания с фото и файлами\n"
        "🔔 **«звонки»** — расписание звонков и перемен\n"
        "🧹 **«дежурные»** — график дежурств по классу\n"
        "⏳ **«сейчас»** — какой сейчас урок и сколько до конца\n"
        "💡 **«факт»** — интересный научный факт\n"
        "🎂 **«др»** — дни рождения одноклассников\n\n"
        "👇 _Или просто нажимайте на кнопки основного меню:_"
    )

    await message.answer(
        help_text,
        reply_markup=get_main_keyboard(is_admin=is_adm, user_id=message.from_user.id),
        parse_mode="Markdown"
    )
