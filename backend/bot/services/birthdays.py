import logging
from datetime import date
from typing import List, Optional
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_today
from backend.db.session import async_session_factory
from backend.db.models import StudentBirthday
from backend.db.crud import (
    get_birthdays_for_date,
    get_approved_group_chats,
    get_class_setting,
    set_class_setting
)
from backend.db.crud.birthdays import MONTH_NAMES_GENITIVE

logger = logging.getLogger(__name__)


def format_birthday_message(students: List[StudentBirthday], target_date: Optional[date] = None) -> str:
    """Формирует красивое и теплое поздравление от имени 11 «Б» класса."""
    if not students:
        return ""

    if target_date is None:
        target_date = get_today()

    day = target_date.day
    month_name = MONTH_NAMES_GENITIVE.get(target_date.month, "сегодня")

    if len(students) == 1:
        names_str = f"✨ **{students[0].full_name}** ✨"
        header_who = "свой день рождения празднует:"
        pronoun = "тебя"
        wish_form = "твой"
    else:
        names_joined = " и ".join(f"**{s.full_name}**" for s in students)
        names_str = f"✨ {names_joined} ✨"
        header_who = "свой день рождения празднуют:"
        pronoun = "вас"
        wish_form = "ваш"

    return (
        "🎉 **С ДНЁМ РОЖДЕНИЯ!** 🎂🎈\n\n"
        f"Сегодня, **{day} {month_name}**, {header_who}\n"
        f"{names_str}\n\n"
        f"От всего сердца поздравляем {pronoun} от имени всего 11 «Б» класса! 🥳\n\n"
        "Желаем:\n"
        "🎯 **Максимальных баллов на ЕГЭ** и легкого поступления в вуз мечты!\n"
        "💪 **Крепкого здоровья**, океана энергии и отличного настроения каждый день!\n"
        "🌟 **Верных друзей**, ярких впечатлений и незабываемого выпускного года!\n"
        f"🚀 Пусть все задуманные планы осуществляются легко, а {wish_form} путь будет наполнен победами!\n\n"
        "С праздником! 🍰🎁✨"
    )


async def check_and_send_birthday_greetings(bot: Bot, force: bool = False) -> int:
    """
    Проверяет, есть ли сегодня именинники в 11 «Б» классе,
    и рассылает праздничное поздравление в беседы класса в топик «Важные объявления».
    Срабатывает ровно в 00:00 (Asia/Yekaterinburg).
    Использует отметку last_birthday_congratulation_date для защиты от дублей при перезагрузках.
    """
    today = get_today()
    today_str = str(today)

    async with async_session_factory() as session:
        if not force:
            last_sent = await get_class_setting(session, "last_birthday_congratulation_date")
            if last_sent == today_str:
                logger.info(f"Birthday greetings for {today_str} were already sent. Skipping.")
                return 0

        birthday_students = await get_birthdays_for_date(session, today.day, today.month)
        if not birthday_students:
            logger.info(f"No birthdays in 11 «Б» on {today.day}.{today.month}. Marking as checked.")
            await set_class_setting(session, "last_birthday_congratulation_date", today_str)
            return 0

        logger.info(f"Found {len(birthday_students)} birthday celebrant(s) today ({today_str}): {[s.full_name for s in birthday_students]}. Sending greetings...")
        msg_text = format_birthday_message(birthday_students, today)

        groups = await get_approved_group_chats(session)
        sent_count = 0

        for g in groups:
            target_thread = g.topic_announcements_id
            kwargs = {"message_thread_id": target_thread} if target_thread else {}
            try:
                await bot.send_message(
                    chat_id=g.chat_id,
                    text=msg_text,
                    parse_mode="Markdown",
                    **kwargs
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Could not send birthday greeting to group {g.chat_id} with thread {target_thread}: {e}")
                if target_thread:
                    try:
                        await bot.send_message(
                            chat_id=g.chat_id,
                            text=msg_text,
                            parse_mode="Markdown"
                        )
                        sent_count += 1
                    except Exception as ex2:
                        logger.error(f"Failed fallback sending birthday greeting to group {g.chat_id}: {ex2}")

        await set_class_setting(session, "last_birthday_congratulation_date", today_str)
        logger.info(f"Birthday greetings successfully sent to {sent_count} group(s).")
        return sent_count
