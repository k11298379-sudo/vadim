from typing import Set

from backend.config import settings
from backend.db.models import User
from backend.natbirzha.config import nat_settings


def get_creator_tg_ids() -> Set[int]:
    """Server-side creator allowlist. Client-provided roles/IDs are never trusted."""
    ids: Set[int] = set()
    if settings.ADMIN_ID:
        ids.add(int(settings.ADMIN_ID))
    raw = (nat_settings.CREATOR_TG_IDS or "").strip()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            ids.add(int(token))
        except ValueError:
            continue
    return ids


def is_creator_user(user: User) -> bool:
    return bool(user.role == "admin" or int(user.tg_id) in get_creator_tg_ids())


__all__ = ["get_creator_tg_ids", "is_creator_user"]
