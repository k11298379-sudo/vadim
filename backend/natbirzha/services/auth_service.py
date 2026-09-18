import hmac
import hashlib
import json
import time
import urllib.parse
from typing import Optional, Dict, Any, Tuple
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.db.session import get_db_session
from backend.db.models import User
from backend.natbirzha.config import nat_settings
from backend.natbirzha.models.company import NatCompany

def validate_strict_telegram_init_data(init_data: str, bot_token: str) -> Optional[Dict[str, Any]]:
    """
    Cryptographically validates Telegram Mini App initData using HMAC-SHA256.
    Checks auth_date to prevent replay attacks (24h validity).
    """
    if not init_data:
        return None

    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed:
            return None

        received_hash = parsed.pop("hash")
        parsed.pop("signature", None)  # Remove signature from Telegram 7.0+

        # Check auth_date for replay attack prevention (max 24h old)
        auth_date = int(parsed.get("auth_date", 0))
        if auth_date > 0 and (time.time() - auth_date) > 86400:
            return None

        # Build data check string
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        secret_key = hmac.new(b"WebAppData", bot_token.strip().encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        if "user" in parsed:
            parsed["user"] = json.loads(parsed["user"])
        return parsed
    except Exception:
        return None

def validate_test_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    """Allows testing when ALLOW_TEST_AUTH is enabled using dedicated TEST_AUTH_SECRET or dev user payload."""
    if not nat_settings.ALLOW_TEST_AUTH or not init_data:
        return None

    # 1. First attempt strict HMAC validation against TEST_AUTH_SECRET (used by integration tests)
    hmac_res = validate_strict_telegram_init_data(init_data, nat_settings.TEST_AUTH_SECRET)
    if hmac_res:
        return hmac_res

    # 2. Local browser fallback when ALLOW_TEST_AUTH is True (e.g. user={"id": 12345, ...})
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        if "user" in parsed:
            user_raw = parsed["user"]
            user_data = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
            if isinstance(user_data, dict) and user_data.get("id"):
                return {"user": user_data}
    except Exception:
        pass

    return None


async def get_strict_natbirzha_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    session: AsyncSession = Depends(get_db_session)
) -> User:
    """
    STRICT AUTH DEPENDENCY:
    Derives authoritative user identity solely from validated Telegram Mini App initData.
    Rejects query params, unvalidated headers, cached UIDs, or localStorage overrides.
    """
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="Strict authentication required: missing X-Telegram-Init-Data header."
        )

    validated = None
    if settings.BOT_TOKEN and ":" in settings.BOT_TOKEN:
        validated = validate_strict_telegram_init_data(x_telegram_init_data, settings.BOT_TOKEN)

    if not validated and nat_settings.ALLOW_TEST_AUTH:
        validated = validate_test_init_data(x_telegram_init_data)

    if not validated or "user" not in validated or not validated["user"].get("id"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Telegram Mini App authentication signature."
        )

    tg_user_data = validated["user"]
    tg_id = int(tg_user_data["id"])

    # Find or create User
    res = await session.execute(select(User).where(User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if not user:
        first = tg_user_data.get("first_name", "")
        last = tg_user_data.get("last_name", "")
        full_name = f"{first} {last}".strip() or "Трейдер НАТБИРЖИ"
        user = User(
            tg_id=tg_id,
            username=tg_user_data.get("username"),
            full_name=full_name,
            role="student"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


async def get_current_company(
    user: User = Depends(get_strict_natbirzha_user),
    session: AsyncSession = Depends(get_db_session)
) -> NatCompany:
    """Returns the NatCompany owned by the strictly authenticated user."""
    res = await session.execute(select(NatCompany).where(NatCompany.user_id == user.id))
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Onboarding required."
        )
    return company
