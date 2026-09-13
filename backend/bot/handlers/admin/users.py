import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.models import User
from backend.db.crud import (
    get_pending_users, get_pending_group_chats, get_active_users,
    get_approved_group_chats, get_user_by_tg_id, update_user_role,
    get_all_users, delete_user, update_user_custom_name
)
from backend.bot.keyboards.admin_kb import get_admin_panel_keyboard, get_cancel_keyboard
from backend.bot.keyboards.main_menu import get_main_keyboard
from backend.bot.keyboards.inline import get_admin_approval_keyboard
from backend.bot.handlers.group import get_admin_chat_approval_keyboard
from backend.bot.handlers.admin.helpers import is_admin
from backend.bot.handlers.admin.states import RenameUserStates
from backend.bot.services.notifier import escape_md

logger = logging.getLogger(__name__)

router = Router(name="admin_users_router")


@router.callback_query(F.data == "admin_view_pending")
async def cb_view_pending(callback: CallbackQuery, db_session: AsyncSession):
    pending_users = await get_pending_users(db_session)
    pending_groups = await get_pending_group_chats(db_session)

    if not pending_users and not pending_groups:
        await callback.message.edit_text(
            "✅ Нет заявок, ожидающих рассмотрения.",
            reply_markup=get_admin_panel_keyboard()
        )
        try:
            await callback.answer()
        except Exception:
            pass
        return

    await callback.message.edit_text(
        f"👥 **Заявок на рассмотрении:** {len(pending_users)} учеников, {len(pending_groups)} групп\n"
    )

    for u in pending_users:
        safe_full_name = escape_md(u.full_name)
        uname = f"@{escape_md(u.username)}" if u.username else "без @username"
        msg_text = f"👤 **Ученик:** {safe_full_name}\n🔗 **Telegram:** {uname}"
        kb = get_admin_approval_keyboard(u.tg_id)
        try:
            await callback.message.answer(
                msg_text,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Markdown error sending pending user {u.tg_id}: {e}")
            try:
                plain = f"👤 Ученик: {u.full_name}\n🔗 Telegram: {u.username or 'без @username'}"
                await callback.message.answer(plain, reply_markup=kb)
            except Exception as e2:
                logger.error(f"Failed to send plain pending user {u.tg_id}: {e2}")

    for g in pending_groups:
        safe_title = escape_md(g.title)
        kb_g = get_admin_chat_approval_keyboard(g.chat_id)
        try:
            await callback.message.answer(
                f"👥 **Группа:** {safe_title}",
                reply_markup=kb_g,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Markdown error sending pending group {g.chat_id}: {e}")
            try:
                await callback.message.answer(f"👥 Группа: {g.title}", reply_markup=kb_g)
            except Exception as e2:
                logger.error(f"Failed to send plain pending group {g.chat_id}: {e2}")

    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "admin_view_students")
async def cb_view_students(callback: CallbackQuery, db_session: AsyncSession):
    students = await get_active_users(db_session)
    groups = await get_approved_group_chats(db_session)

    buttons = []
    lines = ["📋 **Управление правами доступа 11 «Б»:**\n"]
    lines.append(f"👤 **Ученики ({len(students)}):**")

    for i, s in enumerate(students, start=1):
        role_label = "👑 [Админ]" if s.role == "admin" else "👤 [Ученик]"
        safe_disp = escape_md(s.display_name)
        uname = f" (@{escape_md(s.username)})" if s.username else ""
        lines.append(f"{i}. {safe_disp}{uname} — {role_label}")

        row = [InlineKeyboardButton(text=f"✏️ {s.display_name[:12]}", callback_data=f"adm_ren_ask_{s.tg_id}")]
        # Don't show role/delete controls for primary owner ADMIN_ID and for the admin themselves!
        if s.tg_id != settings.ADMIN_ID and s.tg_id != callback.from_user.id:
            toggle_text = "Снять админа" if s.role == "admin" else "Сделать админом"
            row.append(InlineKeyboardButton(text=f"👑 {toggle_text}", callback_data=f"adm_toggle_role_{s.tg_id}"))
            row.append(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del_user_ask_{s.tg_id}"))
        buttons.append(row)

    if groups:
        lines.append(f"\n👥 **Авторизованные группы ({len(groups)}):**")
        for j, g in enumerate(groups, start=1):
            lines.append(f"{j}. {escape_md(g.title)} (ID: `{g.chat_id}`)")

    buttons.append([InlineKeyboardButton(text="🗑 Удалить пользователя", callback_data="admin_delete_user")])
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="admin_menu_back")])

    try:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Markdown error in cb_view_students: {e}")
        plain_lines = [l.replace("*", "").replace("`", "").replace("\\", "") for l in lines]
        await callback.message.edit_text(
            "\n".join(plain_lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "admin_change_name")
async def cb_admin_change_name_list(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    students = await get_active_users(db_session)
    if not students:
        await callback.message.edit_text(
            "ℹ️ В базе пока нет зарегистрированных учеников.",
            reply_markup=get_admin_panel_keyboard()
        )
        try:
            await callback.answer()
        except Exception:
            pass
        return

    buttons = []
    for s in students:
        uname = f" (@{s.username})" if s.username else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {s.display_name}{uname}",
                callback_data=f"adm_ren_ask_{s.tg_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_menu_back")])

    await callback.message.edit_text(
        "✏️ **Смена имени ученика в системе**\n\n"
        "Выберите ученика из списка ниже, чтобы изменить его отображаемое имя (оно показывается в Mini App и списках дежурных):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_ren_ask_"))
async def cb_admin_rename_ask(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    target_id = int(callback.data.replace("adm_ren_ask_", ""))
    user = await get_user_by_tg_id(db_session, target_id)

    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await state.set_state(RenameUserStates.entering_name)
    await state.update_data(rename_target_tg_id=target_id)

    safe_name = escape_md(user.display_name)
    safe_uname = f"@{escape_md(user.username)}" if user.username else "без @username"

    md_text = (
        f"✏️ **Изменение имени ученика:**\n\n"
        f"Текущее имя: **{safe_name}**\n"
        f"Telegram: {safe_uname}\n\n"
        "Отправьте в ответ сообщение с новым именем и фамилией (например: `Иван Иванов`):"
    )

    try:
        await callback.message.edit_text(
            md_text,
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Markdown error in cb_admin_rename_ask: {e}")
        plain_text = (
            f"✏️ Изменение имени ученика:\n\n"
            f"Текущее имя: {user.display_name}\n"
            f"Telegram: @{user.username if user.username else 'без @username'}\n\n"
            "Отправьте в ответ сообщение с новым именем и фамилией (например: Иван Иванов):"
        )
        try:
            await callback.message.edit_text(
                plain_text,
                reply_markup=get_cancel_keyboard()
            )
        except Exception as e2:
            logger.error(f"Failed to edit plain text in cb_admin_rename_ask: {e2}")

    try:
        await callback.answer()
    except Exception:
        pass


@router.message(RenameUserStates.entering_name)
async def msg_admin_rename_save(message: Message, state: FSMContext, db_session: AsyncSession):
    new_name = (message.text or "").strip()
    if not new_name or len(new_name) < 2:
        await message.answer("⚠️ Введите корректное имя и фамилию (не менее 2 символов):", reply_markup=get_cancel_keyboard())
        return

    data = await state.get_data()
    target_tg_id = data.get("rename_target_tg_id")
    if not target_tg_id:
        await state.clear()
        return

    await update_user_custom_name(db_session, target_tg_id, new_name)
    await state.clear()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить еще имя", callback_data="admin_change_name")],
            [InlineKeyboardButton(text="🔙 В панель управления", callback_data="admin_menu_back")]
        ]
    )
    safe_new_name = escape_md(new_name)
    try:
        await message.answer(
            f"✅ Имя ученика успешно изменено на: **{safe_new_name}**!\n\n"
            "Оно обновлено в системе, списках дежурных и Mini App.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception:
        await message.answer(
            f"✅ Имя ученика успешно изменено на: {new_name}!\n\n"
            "Оно обновлено в системе, списках дежурных и Mini App.",
            reply_markup=kb
        )




@router.callback_query(F.data.startswith("adm_toggle_role_"))
async def cb_toggle_user_role(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    target_id = int(callback.data.replace("adm_toggle_role_", ""))
    if target_id == callback.from_user.id:
        await callback.answer("❌ Вы не можете снять права администратора с самого себя!", show_alert=True)
        return

    user = await get_user_by_tg_id(db_session, target_id)
    if user and user.tg_id != settings.ADMIN_ID:
        new_role = "student" if user.role == "admin" else "admin"
        await update_user_role(db_session, target_id, new_role)
        role_label = "Администратор" if new_role == "admin" else "Ученик"
        try:
            await callback.answer(f"Роль изменена на: {role_label}!", show_alert=True)
        except Exception:
            pass

        # Отправляем уведомление и моментально обновляем меню у пользователя
        if new_role == "admin":
            try:
                await callback.bot.send_message(
                    chat_id=target_id,
                    text=(
                        "👑 **Вам предоставлены права администратора класса 11 «Б»!**\n\n"
                        "Вам открыт доступ к **«👑 Панель управления»** (появилась в кнопках внизу чата). "
                        "Вы можете редактировать расписание уроков, звонков и домашние задания."
                    ),
                    reply_markup=get_main_keyboard(is_admin=True, user_id=target_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Could not notify new admin: {e}")
        else:
            try:
                await callback.bot.send_message(
                    chat_id=target_id,
                    text="ℹ️ Ваши права администратора были отозваны. Панель управления закрыта.",
                    reply_markup=get_main_keyboard(is_admin=False, user_id=target_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Could not notify demoted admin: {e}")

        await cb_view_students(callback, db_session)
    else:
        await callback.answer("Невозможно изменить права главного создателя", show_alert=True)


@router.callback_query(F.data == "admin_delete_user")
async def cb_admin_delete_user_list(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    users = await get_all_users(db_session)
    deletable_users = [u for u in users if u.tg_id != settings.ADMIN_ID and u.tg_id != callback.from_user.id]

    if not deletable_users:
        await callback.message.edit_text(
            "ℹ️ В базе нет других пользователей, доступных для удаления.",
            reply_markup=get_admin_panel_keyboard()
        )
        try:
            await callback.answer()
        except Exception:
            pass
        return

    buttons = []
    for u in deletable_users:
        uname = f" (@{u.username})" if u.username else ""
        role_badge = "👑 [Админ]" if u.role == "admin" else ("⏳ [Заявка]" if u.role == "pending" else ("❌ [Отклонен]" if u.role == "rejected" else "👤 [Ученик]"))
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {u.full_name[:18]}{uname} — {role_badge}",
                callback_data=f"adm_del_user_ask_{u.tg_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="👥 К списку пользователей", callback_data="admin_view_students")])
    buttons.append([InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_menu_back")])

    await callback.message.edit_text(
        "🗑 **Удаление пользователя из базы бота**\n\n"
        "Выберите пользователя, которого нужно удалить.\n"
        "⚠️ _Пользователь будет полностью удален, его доступ аннулирован, а персональный чек-лист очищен._",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_del_user_ask_"))
async def cb_admin_delete_user_ask(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    target_tg_id = int(callback.data.replace("adm_del_user_ask_", ""))
    if target_tg_id == settings.ADMIN_ID:
        await callback.answer("Нельзя удалить главного администратора!", show_alert=True)
        return
    if target_tg_id == callback.from_user.id:
        await callback.answer("❌ Вы не можете удалить самого себя!", show_alert=True)
        return

    target_user = await get_user_by_tg_id(db_session, target_tg_id)
    if not target_user:
        await callback.answer("Пользователь не найден или уже удален", show_alert=True)
        await cb_view_students(callback, db_session)
        return

    uname = f"@{escape_md(target_user.username)}" if target_user.username else "без @username"
    safe_name = escape_md(target_user.full_name)
    role_name = "👑 Администратор" if target_user.role == "admin" else ("⏳ На рассмотрении" if target_user.role == "pending" else ("❌ Отклонен" if target_user.role == "rejected" else "👤 Ученик"))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Да, удалить пользователя!",
                    callback_data=f"adm_del_user_confirm_{target_tg_id}"
                )
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="admin_view_students")
            ]
        ]
    )

    try:
        await callback.message.edit_text(
            f"❓ **Подтверждение удаления пользователя**\n\n"
            f"👤 **Имя:** {safe_name}\n"
            f"🔗 **Telegram:** {uname}\n"
            f"🏷 **Роль:** {role_name}\n\n"
            "⚠️ _Пользователь потеряет доступ к боту. Если он снова нажмет /start, ему придется заново отправлять заявку на регистрацию._",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.edit_text(
            f"❓ Подтверждение удаления пользователя\n\n"
            f"👤 Имя: {target_user.full_name}\n"
            f"🔗 Telegram: {target_user.username or 'нет'}\n"
            f"🏷 Роль: {role_name}\n\n"
            "Пользователь потеряет доступ к боту.",
            reply_markup=kb
        )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_del_user_confirm_"))
async def cb_admin_delete_user_confirm(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    target_tg_id = int(callback.data.replace("adm_del_user_confirm_", ""))
    if target_tg_id == settings.ADMIN_ID:
        await callback.answer("Нельзя удалить главного администратора!", show_alert=True)
        return
    if target_tg_id == callback.from_user.id:
        await callback.answer("❌ Вы не можете удалить самого себя!", show_alert=True)
        return

    target_user = await get_user_by_tg_id(db_session, target_tg_id)
    user_name = target_user.full_name if target_user else f"ID {target_tg_id}"
    safe_user_name = escape_md(user_name)

    success = await delete_user(db_session, target_tg_id)
    if success:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👥 К списку пользователей", callback_data="admin_view_students")],
                [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_menu_back")]
            ]
        )
        try:
            await callback.message.edit_text(
                f"✅ **Пользователь {safe_user_name} успешно удален.**\n\n"
                "Его доступ к боту аннулирован, а персональный чек-лист очищен.",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except Exception:
            await callback.message.edit_text(
                f"✅ Пользователь {user_name} успешно удален.\n\n"
                "Его доступ к боту аннулирован, а персональный чек-лист очищен.",
                reply_markup=kb
            )
    else:
        await callback.message.edit_text(
            "⚠️ Не удалось удалить пользователя (возможно, он уже был удален).",
            reply_markup=get_admin_panel_keyboard()
        )
    try:
        await callback.answer()
    except Exception:
        pass
