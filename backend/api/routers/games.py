import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db_session
from backend.db.models import User
from backend.api.auth import get_optional_webapp_user, extract_viewer_tg_id as _extract_viewer_tg_id
from backend.api.game_rooms import game_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["games"])

@router.get("/games/classmates")
async def get_classmates_for_game(
    request: Request,
    tg_user_id: Optional[int] = Query(None),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Возвращает список одноклассников для вызова на онлайн-дуэль."""
    from backend.db.crud import get_active_users
    users = await get_active_users(session)
    current_tg_id = _extract_viewer_tg_id(user, request, query_tg_id=tg_user_id) or 0

    return [
        {
            "id": u.id,
            "tg_id": u.tg_id,
            "name": u.display_name,
            "role": u.role
        }
        for u in users
        if u.tg_id != current_tg_id and u.tg_id > 0
    ]


def _get_public_webapp_url(request: Request) -> str:
    """Returns reliable public HTTPS URL of the Mini App, auto-detecting proxy/tunnel domains."""
    from backend.config import settings
    configured = settings.WEBAPP_URL.strip() if settings.WEBAPP_URL else ""
    if configured and not ("localhost" in configured or "127.0.0.1" in configured):
        return configured

    ref = request.headers.get("referer")
    if ref and ref.startswith("https://"):
        return ref.split("?")[0].split("#")[0]

    origin = request.headers.get("origin")
    if origin and origin.startswith("https://"):
        return f"{origin.rstrip('/')}/app"

    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    proto = request.headers.get("x-forwarded-proto", "https")
    if host and not ("localhost" in host or "127.0.0.1" in host):
        return f"{proto}://{host}/app"

    return configured or "https://t.me"


async def _send_game_invite_notification(
    bot,
    opponent_tg_id: int,
    invite_text: str,
    reply_markup
):
    """Sends invitation to opponent in the background without blocking the HTTP request."""
    try:
        await asyncio.wait_for(
            bot.send_message(
                chat_id=opponent_tg_id,
                text=invite_text,
                reply_markup=reply_markup
            ),
            timeout=8.0
        )
        logger.info(f"Game invitation notification sent to {opponent_tg_id}")
    except Exception as e:
        logger.warning(f"Could not deliver game invitation to {opponent_tg_id}: {e}")


@router.post("/games/local")
async def create_local_game(
    request: Request,
    payload: Optional[Dict[str, Any]] = Body(default=None),
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Создает локальную комнату для 2 игроков на одном устройстве."""
    try:
        if not payload:
            try:
                payload = await request.json()
            except Exception:
                payload = {}

        if not isinstance(payload, dict):
            payload = {}

        game_type = str(payload.get("game_type") or "chess").strip().lower()
        host_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0
        host_name = user.display_name if user else payload.get("host_name", "Белые")

        from backend.api.game_rooms import game_manager, chess
        if game_type == "chess" and chess is None:
            raise HTTPException(
                status_code=503,
                detail="Шахматный режим загружается на сервере. Пожалуйста, подождите минуту!"
            )

        room = game_manager.create_local_room(
            host_tg_id=host_tg_id,
            host_name=host_name,
            game_type=game_type
        )
        return room.to_dict(viewer_tg_id=host_tg_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_local_game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@router.post("/games/invite")
async def invite_opponent_to_game(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: Optional[Dict[str, Any]] = Body(default=None),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Создает комнату и отправляет сообщение с вызовом сопернику в ЛС бота."""
    try:
        if not payload:
            try:
                payload = await request.json()
            except Exception:
                payload = {}

        if not isinstance(payload, dict):
            payload = {}

        try:
            opponent_tg_id = int(payload.get("opponent_tg_id") or 0)
        except (ValueError, TypeError):
            opponent_tg_id = 0

        if not opponent_tg_id:
            raise HTTPException(status_code=400, detail="opponent_tg_id is required")

        game_type = str(payload.get("game_type") or "tictactoe").strip().lower()
        host_color = str(payload.get("host_color") or "white").strip().lower()
        host_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0
        host_name = user.display_name if user else payload.get("host_name", "Одноклассник")

        from backend.api.game_rooms import game_manager, chess
        if game_type == "chess" and chess is None:
            raise HTTPException(
                status_code=503,
                detail="Шахматный режим загружается на сервере. Пожалуйста, подождите минуту или сыграйте в Крестики-нолики!"
            )

        opp_name = payload.get("opponent_name")
        if not opp_name:
            try:
                from backend.db.crud import get_user_by_tg_id
                opp_user = await get_user_by_tg_id(session, opponent_tg_id)
                opp_name = opp_user.display_name if opp_user else "Одноклассник"
            except Exception as ex:
                logger.warning(f"Could not get opponent user from DB: {ex}")
                opp_name = "Одноклассник"

        room = game_manager.create_room(
            host_tg_id=host_tg_id,
            host_name=host_name,
            opponent_tg_id=opponent_tg_id,
            opponent_name=opp_name,
            game_type=game_type,
            host_color=host_color
        )

        from backend.bot.bot import get_current_bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

        bot = get_current_bot()
        bot_notified = False
        if bot and opponent_tg_id:
            try:
                base_url = _get_public_webapp_url(request)
                separator = "&" if "?" in base_url else "?"
                escaped_host_name = html.escape(str(host_name or "Одноклассник"))

                if game_type == "chess":
                    game_url = f"{base_url}{separator}room={room.room_id}&game=chess&tg_user_id={opponent_tg_id}"
                    host_color_actual = getattr(room, "host_color", "white")
                    if host_color_actual == "black":
                        color_line = "Твой цвет: <b>Белые ⚪</b> <i>(ходишь первым!)</i>"
                    else:
                        color_line = "Твой цвет: <b>Черные ⚫</b>"
                    if host_color == "random":
                        color_line += "\n<i>(Цвета определены случайным образом 🎲)</i>"

                    invite_text = (
                        f"♟️ <b>{escaped_host_name}</b> вызывает тебя на <b>Шахматную дуэль</b>!\n"
                        f"{color_line}\n\n"
                        f"⚡ Готов сыграть партию на перемене?"
                    )
                    btn_text = "♟️ Принять вызов и играть"
                else:
                    game_url = f"{base_url}{separator}room={room.room_id}&tg_user_id={opponent_tg_id}"
                    invite_text = (
                        f"🎮 <b>{escaped_host_name}</b> бросает тебе вызов в <b>Крестики-нолики</b>!\n\n"
                        f"⚡ Примешь бой на перемене?"
                    )
                    btn_text = "⚔️ Принять вызов и играть"

                if game_url.startswith("https://"):
                    play_btn = InlineKeyboardButton(
                        text=btn_text,
                        web_app=WebAppInfo(url=game_url)
                    )
                else:
                    play_btn = InlineKeyboardButton(
                        text=btn_text,
                        url=game_url
                    )

                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [play_btn],
                    [
                        InlineKeyboardButton(
                            text="❌ Отклонить",
                            callback_data=f"game_reject:{room.room_id}"
                        )
                    ]
                ])
                background_tasks.add_task(
                    _send_game_invite_notification,
                    bot,
                    opponent_tg_id,
                    invite_text,
                    kb
                )
                bot_notified = True
            except Exception as e:
                logger.warning(f"Error preparing invite notification: {e}")

        res = room.to_dict(viewer_tg_id=host_tg_id)
        res["bot_notified"] = bot_notified
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in invite_opponent_to_game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@router.get("/games/room/{room_id}")
async def get_game_room_state(
    room_id: str,
    request: Request,
    tg_user_id: Optional[int] = Query(None),
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Возвращает текущее состояние игровой комнаты."""
    from backend.api.game_rooms import game_manager
    room = game_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    viewer_tg_id = _extract_viewer_tg_id(user, request, query_tg_id=tg_user_id)
    return room.to_dict(viewer_tg_id=viewer_tg_id)


@router.post("/games/room/{room_id}/join")
async def join_game_room(
    room_id: str,
    request: Request,
    payload: Dict[str, Any] = {},
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Подключение соперника к созданной комнате."""
    from backend.api.game_rooms import game_manager
    viewer_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0
    user_name = user.display_name if user else payload.get("user_name", "Игрок")

    ok, msg = game_manager.join_room(room_id, viewer_tg_id, user_name)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    room = game_manager.get_room(room_id)
    return room.to_dict(viewer_tg_id=viewer_tg_id)


@router.post("/games/room/{room_id}/move")
async def make_game_move(
    room_id: str,
    request: Request,
    payload: Dict[str, Any],
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Ход в игре (Крестики-нолики или Шахматы)."""
    from backend.api.game_rooms import game_manager
    viewer_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0
    move_val = payload.get("move") or payload.get("uci")
    if move_val is None:
        move_val = payload.get("cell")

    ok, msg = game_manager.make_move(room_id, viewer_tg_id, move_val)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    room = game_manager.get_room(room_id)
    return room.to_dict(viewer_tg_id=viewer_tg_id)


@router.post("/games/room/{room_id}/resign")
async def resign_game_room(
    room_id: str,
    request: Request,
    payload: Dict[str, Any] = {},
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Сдача в партии."""
    from backend.api.game_rooms import game_manager
    viewer_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0

    ok, msg = game_manager.resign_room(room_id, viewer_tg_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    room = game_manager.get_room(room_id)
    return room.to_dict(viewer_tg_id=viewer_tg_id)


@router.post("/games/room/{room_id}/rematch")
async def rematch_game_room(
    room_id: str,
    request: Request,
    payload: Dict[str, Any] = {},
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Запрос или подтверждение реванша."""
    from backend.api.game_rooms import game_manager
    viewer_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0

    ok, msg = game_manager.request_rematch(room_id, viewer_tg_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    room = game_manager.get_room(room_id)
    return room.to_dict(viewer_tg_id=viewer_tg_id)


@router.post("/games/room/{room_id}/cancel")
async def cancel_game_room(
    room_id: str,
    request: Request,
    payload: Dict[str, Any] = {},
    user: Optional[User] = Depends(get_optional_webapp_user)
):
    """Отмена вызова создателем."""
    from backend.api.game_rooms import game_manager
    viewer_tg_id = _extract_viewer_tg_id(user, request, payload=payload) or 0
    game_manager.cancel_room(room_id, viewer_tg_id)
    return {"status": "canceled"}


