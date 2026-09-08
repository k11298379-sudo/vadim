import os
from datetime import datetime, date
import zoneinfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")
    ADMIN_ID: int = Field(default=0, description="Telegram ID of the primary administrator")
    TELEGRAM_API_SERVER: str = Field(
        default="",
        description="Custom Telegram Bot API server / reverse proxy (e.g. Cloudflare Worker)"
    )
    
    PORT: int = Field(default=8000, description="Port to listen on")
    HOST: str = Field(default="0.0.0.0", description="Host to listen on")
    BASE_URL: str = Field(default="http://localhost:8000", description="Base URL of the server")
    WEBAPP_URL: str = Field(default="http://localhost:8000/app", description="Public URL for Telegram Mini App")
    
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/bot.db",
        description="Database connection URL"
    )

    
    NOTIFICATION_TIME_EVENING: str = Field(default="19:00", description="Time for daily evening digest (HH:MM)")
    TIMEZONE: str = Field(default="Asia/Yekaterinburg", description="Default timezone (Екатеринбург, UTC+5)")
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API Key for daily facts"
    )

settings = Settings()

def get_today() -> date:
    """Returns today's date according to the configured timezone (Asia/Yekaterinburg)"""
    try:
        tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
        return datetime.now(tz).date()
    except Exception:
        return date.today()

def get_current_date_and_hour() -> tuple[date, int]:
    """Returns (today_date, current_hour 0..23) according to configured timezone (Asia/Yekaterinburg)"""
    try:
        tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
        now = datetime.now(tz)
        return now.date(), now.hour
    except Exception:
        now = datetime.now()
        return now.date(), now.hour

def get_current_date_hour_minute() -> tuple[date, int, int]:
    """Returns (today_date, current_hour, current_minute_slot 0 or 30) according to configured timezone (Asia/Yekaterinburg)"""
    try:
        tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
        now = datetime.now(tz)
        min_slot = 30 if now.minute >= 30 else 0
        return now.date(), now.hour, min_slot
    except Exception:
        now = datetime.now()
        min_slot = 30 if now.minute >= 30 else 0
        return now.date(), now.hour, min_slot


