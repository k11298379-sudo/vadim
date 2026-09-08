import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from backend.config import settings
from backend.bot.services.notifier import (
    send_evening_digest, check_and_send_duty_reminder, send_monday_duty_personal_reminder
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

def setup_scheduler(bot: Bot):
    try:
        hour, minute = settings.NOTIFICATION_TIME_EVENING.split(":")
        trigger = CronTrigger(hour=int(hour), minute=int(minute), timezone=settings.TIMEZONE)

        scheduler.add_job(
            send_evening_digest,
            trigger=trigger,
            args=[bot],
            id="evening_digest_job",
            replace_existing=True
        )

        # Проверка смены дежурных каждое утро в 07:30
        scheduler.add_job(
            check_and_send_duty_reminder,
            trigger=CronTrigger(hour=7, minute=30, timezone=settings.TIMEZONE),
            args=[bot],
            id="duty_rotation_check_job",
            replace_existing=True
        )

        # Персональное напоминание дежурным в понедельник в 06:00 утра
        scheduler.add_job(
            send_monday_duty_personal_reminder,
            trigger=CronTrigger(day_of_week="mon", hour=6, minute=0, timezone=settings.TIMEZONE),
            args=[bot],
            id="monday_duty_personal_reminder_job",
            replace_existing=True
        )

        # Автоматическая очистка устаревших отметок чеклиста и прошлых фактов в 00:05
        async def run_daily_cleanup():
            try:
                from backend.db.session import async_session_factory
                from backend.db.crud.homework import cleanup_past_homework_statuses
                from backend.bot.services.facts import cleanup_past_facts
                async with async_session_factory() as session:
                    cleaned = await cleanup_past_homework_statuses(session)
                    if cleaned > 0:
                        logger.info(f"Daily checklist cleanup: deleted {cleaned} obsolete records from past homework.")
                    cleaned_facts = await cleanup_past_facts(session)
                    if cleaned_facts > 0:
                        logger.info(f"Daily facts cleanup: deleted {cleaned_facts} obsolete past facts.")
            except Exception as ex:
                logger.error(f"Error in daily cleanup: {ex}")

        scheduler.add_job(
            run_daily_cleanup,
            trigger=CronTrigger(hour=0, minute=5, timezone=settings.TIMEZONE),
            id="daily_cleanup_job",
            replace_existing=True
        )

        # Автоматическая генерация интересного факта каждые полчаса (:00 и :30)
        async def run_half_hour_fact_generation():
            try:
                from backend.db.session import async_session_factory
                from backend.bot.services.facts import get_or_generate_slot_fact
                async with async_session_factory() as session:
                    fact = await get_or_generate_slot_fact(session)
                    logger.info(f"Interesting fact ready for {fact.date} {fact.hour:02d}:{fact.minute:02d}: '{fact.title}' ({fact.category})")
            except Exception as ex:
                logger.error(f"Error pre-generating fact: {ex}")

        scheduler.add_job(
            run_half_hour_fact_generation,
            trigger=CronTrigger(minute="0,30", timezone=settings.TIMEZONE),
            id="half_hour_fact_generation_job",
            replace_existing=True
        )

        scheduler.start()
        logger.info(f"Scheduler started with evening digest ({settings.NOTIFICATION_TIME_EVENING}), duty check (07:30), Monday duty reminder (06:00), fact rotation (every 30m), and daily cleanup (00:05, {settings.TIMEZONE})")


    except Exception as e:
        logger.error(f"Error setting up scheduler: {e}")
