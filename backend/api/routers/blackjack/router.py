"""
FastAPI роутер игры «Блэкджек (21 очко)» на монеты.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Body

from backend.db.models import User
from backend.db.session import async_session_factory
from backend.db.crud.users import add_user_coins, get_user_by_tg_id
from backend.api.auth import get_optional_webapp_user, extract_viewer_tg_id as _extract_viewer_tg_id
from backend.bot.game_blackjack import BlackjackGame
from .state import get_session, create_session, clear_session

router = APIRouter(prefix="/blackjack", tags=["blackjack"])


async def _resolve_user_and_check_ecosystem(
    request: Request,
    user: Optional[User],
) -> tuple[int, User]:
    viewer_id = user.tg_id if user else await _extract_viewer_tg_id(request)
    if not viewer_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram Mini App")

    async with async_session_factory() as session:
        db_user = await get_user_by_tg_id(session, viewer_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        if not bool(getattr(db_user, "currency_ecosystem_enabled", False)):
            raise HTTPException(
                status_code=400,
                detail="Включите игровую экосистему в настройках бота для игры в 21 Очко"
            )
        return viewer_id, db_user


@router.get("/state")
async def blackjack_state(
    request: Request,
    user: Optional[User] = Depends(get_optional_webapp_user),
):
    """Получение текущего состояния раздачи и баланса игрока."""
    viewer_id, db_user = await _resolve_user_and_check_ecosystem(request, user)
    sess = get_session(viewer_id)
    state = sess["game"].to_dict() if sess else None
    return {
        "ok": True,
        "state": state,
        "coins": db_user.coins or 0,
    }


@router.post("/deal")
async def blackjack_deal(
    request: Request,
    payload: Dict[str, Any] = Body(default={}),
    user: Optional[User] = Depends(get_optional_webapp_user),
):
    """
    Начало новой раздачи в Блэкджек.
    payload: {"stake": 25}
    """
    viewer_id, db_user = await _resolve_user_and_check_ecosystem(request, user)

    stake = int(payload.get("stake", 10))
    if stake <= 0:
        raise HTTPException(status_code=400, detail="Ставка должна быть больше 0")

    if (db_user.coins or 0) < stake:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно монет для ставки. Ваш баланс: {db_user.coins or 0} 🪙"
        )

    # Списываем ставку из базы данных
    async with async_session_factory() as session:
        await add_user_coins(session, viewer_id, -stake)
        refreshed_user = await get_user_by_tg_id(session, viewer_id)
        user_coins = refreshed_user.coins or 0

    sess = create_session(viewer_id, stake)
    game: BlackjackGame = sess["game"]
    state = game.deal(stake)

    # Если выпал натуральный Блэкджек или ничья с первых 2 карт
    if game.phase == "done" and not sess["settled"]:
        if game.payout > 0:
            async with async_session_factory() as session:
                await add_user_coins(session, viewer_id, game.payout)
                refreshed_user = await get_user_by_tg_id(session, viewer_id)
                user_coins = refreshed_user.coins or 0
        sess["settled"] = True

    return {
        "ok": True,
        "state": state,
        "coins": user_coins,
    }


@router.post("/hit")
async def blackjack_hit(
    request: Request,
    user: Optional[User] = Depends(get_optional_webapp_user),
):
    """Игрок берет дополнительную карту («Еще»)."""
    viewer_id, db_user = await _resolve_user_and_check_ecosystem(request, user)
    sess = get_session(viewer_id)
    if not sess or sess["game"].phase != "player_turn":
        raise HTTPException(status_code=400, detail="Нет активной раздачи")

    game: BlackjackGame = sess["game"]
    state = game.hit()
    user_coins = db_user.coins or 0

    if game.phase == "done" and not sess["settled"]:
        if game.payout > 0:
            async with async_session_factory() as session:
                await add_user_coins(session, viewer_id, game.payout)
                refreshed_user = await get_user_by_tg_id(session, viewer_id)
                user_coins = refreshed_user.coins or 0
        sess["settled"] = True

    return {
        "ok": True,
        "state": state,
        "coins": user_coins,
    }


@router.post("/stand")
async def blackjack_stand(
    request: Request,
    user: Optional[User] = Depends(get_optional_webapp_user),
):
    """Игрок останавливается («Хватит»). Ход переходит к дилеру."""
    viewer_id, db_user = await _resolve_user_and_check_ecosystem(request, user)
    sess = get_session(viewer_id)
    if not sess or sess["game"].phase != "player_turn":
        raise HTTPException(status_code=400, detail="Нет активной раздачи")

    game: BlackjackGame = sess["game"]
    state = game.stand()
    user_coins = db_user.coins or 0

    if game.phase == "done" and not sess["settled"]:
        if game.payout > 0:
            async with async_session_factory() as session:
                await add_user_coins(session, viewer_id, game.payout)
                refreshed_user = await get_user_by_tg_id(session, viewer_id)
                user_coins = refreshed_user.coins or 0
        sess["settled"] = True

    return {
        "ok": True,
        "state": state,
        "coins": user_coins,
    }


@router.post("/double")
async def blackjack_double(
    request: Request,
    user: Optional[User] = Depends(get_optional_webapp_user),
):
    """Удвоение ставки («Удвоить»): +1 карта и завершение хода."""
    viewer_id, db_user = await _resolve_user_and_check_ecosystem(request, user)
    sess = get_session(viewer_id)
    if not sess or sess["game"].phase != "player_turn":
        raise HTTPException(status_code=400, detail="Нет активной раздачи")

    game: BlackjackGame = sess["game"]
    if len(game.player_cards) != 2:
        raise HTTPException(status_code=400, detail="Удвоить ставку можно только на первых двух картах")

    additional_stake = game.original_stake
    if (db_user.coins or 0) < additional_stake:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно монет для удвоения (требуется еще {additional_stake} 🪙)"
        )

    # Списываем дополнительную ставку
    async with async_session_factory() as session:
        await add_user_coins(session, viewer_id, -additional_stake)

    state = game.double_down()

    async with async_session_factory() as session:
        if game.phase == "done" and not sess["settled"] and game.payout > 0:
            await add_user_coins(session, viewer_id, game.payout)
            sess["settled"] = True
        refreshed_user = await get_user_by_tg_id(session, viewer_id)
        user_coins = refreshed_user.coins or 0

    return {
        "ok": True,
        "state": state,
        "coins": user_coins,
    }
