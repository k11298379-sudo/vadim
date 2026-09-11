from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.crud import (
    toggle_user_canteen_reminder,
    toggle_user_currency_ecosystem,
    get_user_by_tg_id
)
from backend.db.models import User

router = Router(name="settings_router")


def build_settings_keyboard(canteen_on: bool, currency_on: bool) -> InlineKeyboardMarkup:
    canteen_icon = "✅ Вкл" if canteen_on else "⬜ Выкл"
    currency_icon = "✅ Вкл" if currency_on else "⬜ Выкл"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🍽 Столовая (после 5 урока): {canteen_icon}",
                    callback_data="set_canteen_toggle"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🪙 Игровая экосистема: {currency_icon}",
                    callback_data="set_currency_toggle"
                )
            ]
        ]
    )


def format_settings_text(canteen_on: bool, currency_on: bool, coins: int) -> str:
    canteen_status = "🟢 <b>Включено</b> (3 сообщения после 5 урока)" if canteen_on else "⚪ <b>Выключено</b>"
    currency_status = f"🟢 <b>Включена</b> (баланс: <code>{coins}</code> 🪙)" if currency_on else "⚪ <b>Выключена</b>"

    return (
        "⚙️ <b>Настройки профиля 11 «Б»</b>\n\n"
        f"🍽 <b>Напоминание о столовой:</b> {canteen_status}\n"
        "<i>После окончания 5-го урока вам в ЛС придут 3 напоминания, что пора идти обедать.</i>\n\n"
        f"🪙 <b>Внутриигровая экосистема:</b> {currency_status}\n"
        "<i>Разблокирует игру «Дурак», команды <code>/cash</code> и <code>/work</code>, ставки на монеты и рейтинг игроков в Mini App.</i>\n\n"
        "👇 <i>Нажмите на кнопку ниже, чтобы переключить режим:</i>"
    )


@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def show_settings(message: Message, current_user: User):
    canteen_on = bool(getattr(current_user, "canteen_reminder_enabled", False))
    currency_on = bool(getattr(current_user, "currency_ecosystem_enabled", False))
    coins = getattr(current_user, "coins", 100) or 0

    await message.answer(
        format_settings_text(canteen_on, currency_on, coins),
        reply_markup=build_settings_keyboard(canteen_on, currency_on),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "set_canteen_toggle")
async def cb_toggle_canteen(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    new_val = await toggle_user_canteen_reminder(db_session, current_user.tg_id)
    # Refresh user
    user = await get_user_by_tg_id(db_session, current_user.tg_id) or current_user
    currency_on = bool(getattr(user, "currency_ecosystem_enabled", False))
    coins = getattr(user, "coins", 100) or 0

    await callback.message.edit_text(
        format_settings_text(new_val, currency_on, coins),
        reply_markup=build_settings_keyboard(new_val, currency_on),
        parse_mode="HTML"
    )
    status_msg = "✅ Напоминание о столовой включено!" if new_val else "⬜ Напоминание о столовой выключено"
    await callback.answer(status_msg)


@router.callback_query(F.data == "set_currency_toggle")
async def cb_toggle_currency(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    new_val = await toggle_user_currency_ecosystem(db_session, current_user.tg_id)
    # Refresh user
    user = await get_user_by_tg_id(db_session, current_user.tg_id) or current_user
    canteen_on = bool(getattr(user, "canteen_reminder_enabled", False))
    coins = getattr(user, "coins", 100) or 0

    await callback.message.edit_text(
        format_settings_text(canteen_on, new_val, coins),
        reply_markup=build_settings_keyboard(canteen_on, new_val),
        parse_mode="HTML"
    )
    status_msg = (
        "🪙 Игровая экосистема включена! Доступны /cash, /work и игра Дурак со ставками."
        if new_val else
        "⬜ Игровая экосистема выключена"
    )
    await callback.answer(status_msg, show_alert=new_val)
