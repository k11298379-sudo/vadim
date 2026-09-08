from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User
from backend.db.crud import get_notifiable_users, get_approved_group_chats
from backend.bot.keyboards.admin_kb import (
    get_admin_panel_keyboard, get_cancel_keyboard, get_broadcast_destination_keyboard
)
from backend.bot.handlers.admin.helpers import is_admin
from backend.bot.handlers.admin.states import BroadcastStates

router = Router(name="admin_broadcast_router")


@router.callback_query(F.data == "admin_broadcast_custom")
async def cb_admin_broadcast_custom_start(callback: CallbackQuery, state: FSMContext, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return
    await state.set_state(BroadcastStates.entering_message)
    await callback.message.edit_text(
        "📢 **Создание срочного объявления для 11 «Б»**\n\n"
        "Отправьте текст объявления, которое необходимо разослать.\n\n"
        "💡 _Поддерживается форматирование (жирный, курсив, списки). Также можно отправить фотографию с текстом в подписи._",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(BroadcastStates.entering_message)
async def msg_admin_broadcast_text(message: Message, state: FSMContext, current_user: User):
    if not is_admin(current_user, message.from_user.id):
        return

    text = message.text or message.caption or ""
    photo_id = message.photo[-1].file_id if message.photo else None

    if not text and not photo_id:
        await message.answer("⚠️ Пожалуйста, введите текст объявления или отправьте фото с описанием:")
        return

    await state.update_data(broadcast_text=text, photo_id=photo_id)
    await state.set_state(BroadcastStates.confirm_destination)

    preview_text = text if text else "*(без текста, только фото)*"
    prompt_text = (
        "👀 **Предпросмотр объявления:**\n"
        "──────────────────────\n"
        f"{preview_text}\n"
        "──────────────────────\n\n"
        "Куда отправить это объявление?"
    )

    if photo_id:
        await message.answer_photo(
            photo=photo_id,
            caption=prompt_text,
            reply_markup=get_broadcast_destination_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            prompt_text,
            reply_markup=get_broadcast_destination_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(BroadcastStates.confirm_destination, F.data.startswith("bcast_dest_"))
async def cb_admin_broadcast_send(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession, bot: Bot, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    dest = callback.data.replace("bcast_dest_", "")
    data = await state.get_data()
    raw_text = data.get("broadcast_text", "")
    photo_id = data.get("photo_id")

    author_name = current_user.full_name or callback.from_user.full_name or "Администрация"
    final_text = (
        "📢 **СРОЧНОЕ ОБЪЯВЛЕНИЕ • 11 «Б»** 📢\n\n"
        f"{raw_text}\n\n"
        f"✍️ _Опубликовал(а): {author_name}_"
    )

    sent_users = 0
    sent_groups = 0

    if dest in ["users", "all"]:
        users = await get_notifiable_users(db_session)
        for u in users:
            try:
                if photo_id:
                    await bot.send_photo(chat_id=u.tg_id, photo=photo_id, caption=final_text, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=u.tg_id, text=final_text, parse_mode="Markdown")
                sent_users += 1
            except Exception:
                pass

    if dest in ["groups", "all"]:
        groups = await get_approved_group_chats(db_session)
        for g in groups:
            try:
                if photo_id:
                    await bot.send_photo(chat_id=g.chat_id, message_thread_id=g.topic_announcements_id, photo=photo_id, caption=final_text, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=g.chat_id, message_thread_id=g.topic_announcements_id, text=final_text, parse_mode="Markdown")
                sent_groups += 1
            except Exception:
                pass

    total_sent = sent_users + sent_groups
    dest_label = "всему классу (в ЛС)" if dest == "users" else ("в беседы" if dest == "groups" else "всему классу и в беседы")

    await state.clear()
    result_msg = (
        f"✅ **Объявление успешно разослано {dest_label}!**\n\n"
        f"📊 **Получателей:** {total_sent} (учеников: {sent_users}, бесед: {sent_groups})"
    )

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(result_msg, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    else:
        await callback.message.edit_text(result_msg, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
    try:
        await callback.answer("Объявление отправлено!", show_alert=True)
    except Exception:
        pass
