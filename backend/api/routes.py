from datetime import date, datetime
from typing import List, Optional, Dict, Any
import html
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request, BackgroundTasks, Body
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


from backend.db.session import get_db_session
from backend.db.models import User
from backend.api.auth import get_current_webapp_user, get_optional_webapp_user
from backend.db.crud import (
    get_schedule_for_day, get_schedule_for_date, get_full_week_schedule, get_bell_schedule,
    get_bell_schedule_for_date,
    get_substitutions_for_date, get_homework_for_date,
    get_homework_by_subject, get_all_subjects,
    toggle_homework_completion, get_user_homework_status,
    get_current_duty_info
)

from backend.config import get_today

api_router = APIRouter(prefix="/api")


@api_router.get("/me")
async def get_me(user: Optional[User] = Depends(get_optional_webapp_user)):
    if user:
        return {
            "id": user.id,
            "tg_id": user.tg_id,
            "full_name": user.display_name,
            "custom_name": user.custom_name,
            "role": user.role,
            "class_name": "11 «Б»",
            "notifications_enabled": user.notifications_enabled
        }

    return {
        "id": 0,
        "tg_id": 0,
        "full_name": "",
        "role": "student",
        "class_name": "11 «Б»",
        "notifications_enabled": False
    }


@api_router.get("/bells")
async def get_bells(session: AsyncSession = Depends(get_db_session)):
    bells = await get_bell_schedule(session)
    return [
        {
            "lesson_number": b.lesson_number,
            "start_time": b.start_time,
            "end_time": b.end_time,
            "break_duration": b.break_duration
        }
        for b in bells
    ]

@api_router.get("/subjects")
async def get_subjects(session: AsyncSession = Depends(get_db_session)):
    subjects = await get_all_subjects(session)
    return [
        {
            "id": s.id,
            "name": s.name,
            "teacher_name": s.teacher_name
        }
        for s in subjects
    ]

@api_router.get("/students")
async def get_students_api(session: AsyncSession = Depends(get_db_session)):
    from backend.db.crud import get_active_users
    users = await get_active_users(session)
    return [
        {
            "id": u.id,
            "tg_id": u.tg_id,
            "name": u.display_name,
            "role": u.role
        }
        for u in users
    ]

@api_router.get("/schedule")
async def get_schedule(
    target_date: Optional[str] = Query(None, description="ISO format date YYYY-MM-DD"),
    session: AsyncSession = Depends(get_db_session)
):
    if target_date:
        query_date = date.fromisoformat(target_date)
    else:
        query_date = get_today()


    day_of_week = query_date.isoweekday()
    schedules = await get_schedule_for_date(session, query_date)
    subs = await get_substitutions_for_date(session, query_date)

    bells = {b.lesson_number: b for b in await get_bell_schedule_for_date(session, query_date)}


    # Merge schedule with substitutions and bells
    sub_map = {s.lesson_number: s for s in subs}
    lessons = []
    
    max_lesson = max(
        [s.lesson_number for s in schedules] + [s.lesson_number for s in subs] or [0]
    )

    sched_map = {s.lesson_number: s for s in schedules}

    for num in range(1, max_lesson + 1):
        bell = bells.get(num)
        base = sched_map.get(num)
        sub = sub_map.get(num)

        lesson_item = {
            "lesson_number": num,
            "start_time": bell.start_time if bell else "",
            "end_time": bell.end_time if bell else "",
            "is_substitution": False,
            "is_cancelled": False,
            "subject_name": "",
            "comment": ""
        }

        if sub:
            if sub.is_cancelled:
                continue
            lesson_item["is_substitution"] = True
            lesson_item["is_cancelled"] = False
            lesson_item["comment"] = sub.comment or ""
            lesson_item["subject_name"] = sub.new_subject.name if sub.new_subject else (base.subject.name if base else "Урок")
            lessons.append(lesson_item)
        elif base:
            lesson_item["subject_name"] = base.subject.name if base.subject else "Урок"
            lessons.append(lesson_item)


    from backend.bot.services.academic_calendar import get_day_special_status
    day_status, status_text = get_day_special_status(query_date)

    return {
        "date": query_date.isoformat(),
        "day_of_week": day_of_week,
        "class_name": "11 «Б»",
        "day_status": day_status,
        "status_text": status_text,
        "lessons": lessons
    }


@api_router.get("/schedule/week")
async def get_week_schedule(session: AsyncSession = Depends(get_db_session)):
    week_map = await get_full_week_schedule(session)
    bells = {b.lesson_number: b for b in await get_bell_schedule(session)}

    result = {}
    for day_num, items in week_map.items():
        lessons = []
        for it in items:
            bell = bells.get(it.lesson_number)
            lessons.append({
                "lesson_number": it.lesson_number,
                "start_time": bell.start_time if bell else "",
                "end_time": bell.end_time if bell else "",
                "subject_name": it.subject.name
            })
        result[day_num] = lessons

    return result

@api_router.get("/homework")
async def get_homework(
    target_date: Optional[str] = Query(None, description="ISO format date YYYY-MM-DD"),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    if target_date:
        query_date = date.fromisoformat(target_date)
    else:
        query_date = get_today()

    homeworks = await get_homework_for_date(session, query_date)

    result = []
    for hw in homeworks:
        status = None
        if user:
            status = await get_user_homework_status(session, user.id, hw.id)
        enriched_atts = []
        for a in (hw.attachments or []):
            item = dict(a)
            if item.get("file_id"):
                item["url"] = f"/api/media/{item['file_id']}"
            enriched_atts.append(item)


        result.append({
            "id": hw.id,
            "subject_name": hw.subject.name,
            "due_date": hw.due_date.isoformat(),
            "title": hw.title,
            "description": hw.description,
            "attachments": enriched_atts,
            "is_completed": status.is_completed if status else False
        })
    return result


@api_router.post("/homework/{hw_id}/toggle")
async def toggle_homework(
    hw_id: int,
    user: User = Depends(get_current_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    new_status = await toggle_homework_completion(session, user.id, hw_id)
    return {"id": hw_id, "is_completed": new_status}


@api_router.get("/duty")
async def get_duty_info(session: AsyncSession = Depends(get_db_session)):
    active_group, all_groups = await get_current_duty_info(session)
    return {
        "current_group": active_group.group_number if active_group is not None else 0,
        "name": active_group.name if active_group else "Группа 0",
        "members": active_group.members if active_group else "Не назначено",

        "all_groups": [
            {
                "group_number": g.group_number,
                "name": g.name,
                "members": g.members,
                "is_active": (active_group and g.group_number == active_group.group_number)
            }
            for g in all_groups
        ]
    }


@api_router.get("/facts/today")
async def get_today_fact_endpoint(
    response: Response,
    target_date: Optional[str] = Query(None, description="ISO format date YYYY-MM-DD"),
    target_hour: Optional[int] = Query(None, ge=0, le=23, description="Hour of the day 0..23"),
    target_minute: Optional[int] = Query(None, ge=0, le=59, description="Minute 0..59"),
    session: AsyncSession = Depends(get_db_session)
):
    """Возвращает единый интересный факт каждые полчаса для всех учеников."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    from backend.bot.services.facts import get_or_generate_slot_fact
    query_date = None
    if target_date:
        try:
            query_date = date.fromisoformat(target_date)
        except ValueError:
            pass
    fact = await get_or_generate_slot_fact(
        session,
        target_date=query_date,
        target_hour=target_hour,
        target_minute=target_minute
    )
    return {
        "date": fact.date.isoformat(),
        "hour": fact.hour,
        "minute": fact.minute,
        "category": fact.category,
        "title": fact.title,
        "fact": fact.fact_text
    }


@api_router.get("/bells")
async def get_bells_api(
    target_date: Optional[str] = Query(None, description="ISO format date YYYY-MM-DD"),
    session: AsyncSession = Depends(get_db_session)
):
    if target_date:
        query_date = date.fromisoformat(target_date)
        bells = await get_bell_schedule_for_date(session, query_date)
    else:
        bells = await get_bell_schedule_for_date(session, get_today())
    return [
        {
            "lesson_number": b.lesson_number,
            "start_time": b.start_time,
            "end_time": b.end_time,
            "break_duration": b.break_duration
        }
        for b in bells
    ]


@api_router.get("/media/{file_id}")
async def get_telegram_media(file_id: str):
    """
    Проксирует фотографии и файлы из Telegram Bot API в Mini App,
    позволяя просматривать их в полном качестве и скачивать без раскрытия токена.
    """
    from backend.main import bot
    from backend.config import settings

    try:
        file_info = await bot.get_file(file_id)
        if not file_info.file_path:
            raise HTTPException(status_code=404, detail="File path not found in Telegram")

        file_url = f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_info.file_path}"
        async with httpx.AsyncClient() as client:
            tg_resp = await client.get(file_url, timeout=25.0)
            if tg_resp.status_code != 200:
                raise HTTPException(status_code=tg_resp.status_code, detail="Failed to fetch media from Telegram")

            content_type = tg_resp.headers.get("content-type", "image/jpeg")
            filename = file_info.file_path.split("/")[-1]
            return Response(
                content=tg_resp.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Content-Disposition": f"inline; filename=\"{filename}\""
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# MULTIPLAYER GAMES API (Крестики-нолики онлайн с вызовом через бота)
# ==============================================================================

def _extract_viewer_tg_id(
    user: Optional[User],
    request: Request,
    payload: Optional[Dict[str, Any]] = None,
    query_tg_id: Optional[int] = None
) -> Optional[int]:
    if user and user.tg_id:
        return user.tg_id
    if payload and payload.get("tg_user_id"):
        try:
            return int(payload["tg_user_id"])
        except Exception:
            pass
    if query_tg_id:
        return query_tg_id
    hdr = request.headers.get("x-telegram-user-id") or request.headers.get("X-Telegram-User-Id")
    if hdr:
        try:
            return int(hdr)
        except Exception:
            pass
    q = request.query_params.get("tg_user_id") or request.query_params.get("uid")
    if q:
        try:
            return int(q)
        except Exception:
            pass
    return None


@api_router.get("/games/classmates")
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


@api_router.post("/games/invite")
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


@api_router.get("/games/room/{room_id}")
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


@api_router.post("/games/room/{room_id}/join")
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


@api_router.post("/games/room/{room_id}/move")
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


@api_router.post("/games/room/{room_id}/resign")
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


@api_router.post("/games/room/{room_id}/rematch")
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


@api_router.post("/games/room/{room_id}/cancel")
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



