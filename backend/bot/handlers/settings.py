from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.crud import toggle_user_notifications
from backend.bot.keyboards.inline import get_settings_keyboard
from backend.db.models import User

router = Router(name="settings_router")

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):

    await message.answer(
        "🔔 **Уведомления и рассылка 11 «Б»:**\n\n"
        "Вечерняя рассылка с расписанием и домашним заданием на завтра включена **по умолчанию** и отправляется каждый день в 19:00.\n\n"
        "Никаких дополнительных настроек не требуется!",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data == "toggle_notifications")
async def cb_toggle_notifications(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    new_val = await toggle_user_notifications(db_session, current_user.id)
    await callback.message.edit_reply_markup(reply_markup=get_settings_keyboard(new_val))
    status_str = "включены" if new_val else "выключены"
    await callback.answer(f"Уведомления {status_str}!")
