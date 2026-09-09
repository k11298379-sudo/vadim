import time
import asyncio
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User, Subject
from backend.db.crud import (
    get_all_subjects, get_subject_by_id, create_homework, delete_homework,
    get_recent_active_homeworks, get_homework_by_id, find_upcoming_dates_for_subject
)
from backend.bot.keyboards.admin_kb import (
    get_admin_panel_keyboard, get_cancel_keyboard, get_hw_notify_keyboard
)
from backend.bot.keyboards.calendar import get_inline_calendar
from backend.bot.services.notifier import send_new_homework_alert
from backend.bot.handlers.schedule import DAYS_RU
from backend.bot.handlers.admin.helpers import is_admin
from backend.bot.handlers.admin.states import AddHomeworkStates

router = Router(name="admin_homework_router")


# ==================== HELPERS & FORMATTING ====================

SUBJECT_ICONS = {
    "Русский язык": "📖",
    "Литература": "📚",
    "Алгебра": "📐",
    "Геометрия": "📏",
    "Физика": "⚡",
    "Химия": "🧪",
    "Биология": "🌿",
    "История": "🏛",
    "Обществознание": "⚖️",
    "География": "🌍",
    "Английский язык": "🇬🇧",
    "Информатика": "💻",
    "Физкультура": "⚽",
    "ОБЖ": "🛡",
    "ВИС": "🎓",
}

SUBJECT_ALIASES = {
    "русский": "Русский язык",
    "русский язык": "Русский язык",
    "рус": "Русский язык",
    "рус яз": "Русский язык",
    "русяз": "Русский язык",
    "литература": "Литература",
    "литра": "Литература",
    "лит-ра": "Литература",
    "лит": "Литература",
    "алгебра": "Алгебра",
    "алг": "Алгебра",
    "математика": "Алгебра",
    "матеша": "Алгебра",
    "геометрия": "Геометрия",
    "геома": "Геометрия",
    "геом": "Геометрия",
    "физика": "Физика",
    "физ": "Физика",
    "химия": "Химия",
    "хим": "Химия",
    "биология": "Биология",
    "био": "Биология",
    "история": "История",
    "ист": "История",
    "обществознание": "Обществознание",
    "общество": "Обществознание",
    "общага": "Обществознание",
    "география": "География",
    "гео": "География",
    "английский": "Английский язык",
    "английский язык": "Английский язык",
    "англ": "Английский язык",
    "англ яз": "Английский язык",
    "инглиш": "Английский язык",
    "информатика": "Информатика",
    "инфа": "Информатика",
    "ит": "Информатика",
    "it": "Информатика",
    "информационные технологии": "Информатика",
    "физкультура": "Физкультура",
    "физра": "Физкультура",
    "спорт": "Физкультура",
    "обж": "ОБЖ",
    "основы безопасности": "ОБЖ",
    "вис": "ВИС",
}


def escape_md(text: str) -> str:
    r"""Экранирует спецсимволы Markdown v1: \, _, *, `, ["""
    if not text:
        return ""
    for ch in ["\\", "_", "*", "`", "["]:
        text = text.replace(ch, f"\\{ch}")
    return text


async def safe_answer(message: Message, text: str, reply_markup=None) -> Optional[Message]:
    """Отправляет сообщение с Markdown разметкой; при синтаксических ошибках откатывается к чистому тексту."""
    try:
        return await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        plain = text.replace("**", "").replace("*", "").replace("`", "").replace("_", "")
        return await message.answer(plain, reply_markup=reply_markup, parse_mode=None)


async def safe_edit_text(message_or_query, text: str, reply_markup=None):
    """Редактирует сообщение с Markdown разметкой; при ошибках парсинга откатывается к чистому тексту."""
    msg = message_or_query.message if hasattr(message_or_query, "message") else message_or_query
    try:
        return await msg.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        plain = text.replace("**", "").replace("*", "").replace("`", "").replace("_", "")
        return await msg.edit_text(plain, reply_markup=reply_markup, parse_mode=None)


def find_subject_by_text(text: str, subjects: List[Subject]) -> Optional[Subject]:
    """Находит предмет по точному совпадению, списку синонимов или частичному вхождению."""
    clean = text.strip().lower()
    if not clean:
        return None

    # 1. Проверяем словарь алиасов
    target_name = SUBJECT_ALIASES.get(clean)
    if target_name:
        for s in subjects:
            if s.name.lower() == target_name.lower():
                return s

    # 2. Точное совпадение (регистронезависимо)
    for s in subjects:
        if s.name.lower() == clean:
            return s

    # 3. Совпадение по началу или вхождению
    for s in subjects:
        s_low = s.name.lower()
        if clean in s_low or s_low in clean:
            return s

    return None


def build_subjects_keyboard_grid(subjects: List[Subject]) -> InlineKeyboardMarkup:
    """Генерирует компактную 2-колоночную клавиатуру выбора предметов с иконками."""
    buttons = []
    row = []
    for s in subjects:
        icon = SUBJECT_ICONS.get(s.name, "📚")
        btn = InlineKeyboardButton(text=f"{icon} {s.name}", callback_data=f"adm_hw_s_{s.id}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_upcoming_or_fallback_dates(
    db_session: AsyncSession,
    subject_id: int,
    from_date: date,
    limit: int = 4
) -> Tuple[List[date], bool]:
    """
    Возвращает (список_дат, есть_ли_в_расписании).
    Если предмет стоит в расписании уроков, возвращает дни уроков.
    Если расписание для предмета не заполнено (или уроков меньше limit),
    дополняет ближайшими учебными днями (Пн-Сб, пропуская Вс).
    """
    scheduled = await find_upcoming_dates_for_subject(db_session, subject_id, from_date=from_date, limit=limit)
    is_scheduled = bool(scheduled)
    dates = list(scheduled)

    cur = from_date
    while len(dates) < limit:
        # Пропускаем воскресенье (7) и уже имеющиеся даты
        if cur.isoweekday() != 7 and cur not in dates:
            dates.append(cur)
        cur += timedelta(days=1)

    dates.sort()
    return dates, is_scheduled


def build_date_keyboard(dates: List[date], selected_date: date, is_scheduled: bool) -> InlineKeyboardMarkup:
    """Строит инлайн-клавиатуру выбора дат сдачи."""
    date_btns = []
    for i, d in enumerate(dates):
        d_name = DAYS_RU.get(d.isoweekday(), "")
        is_cur = (d == selected_date)
        if is_cur:
            icon = "✅"
        elif i == 0 and is_scheduled:
            icon = "⭐"
        else:
            icon = "📅"
        suffix = " — След. урок" if (i == 0 and is_scheduled) else ""
        label = f"{icon} {d_name} ({d.strftime('%d.%m')}){suffix}"
        date_btns.append([InlineKeyboardButton(text=label, callback_data=f"adm_hw_d_{d.isoformat()}")])

    date_btns.append([InlineKeyboardButton(text="🗓 Другая дата на календаре", callback_data="adm_hw_open_cal")])
    date_btns.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=date_btns)


async def proceed_to_entering_content(
    target_msg,  # CallbackQuery or Message
    state: FSMContext,
    db_session: AsyncSession,
    subject_id: int
):
    """Общий переход к шагу ввода задания после выбора предмета (кнопкой или текстом)."""
    subj = await get_subject_by_id(db_session, subject_id)
    subj_name = subj.name if subj else "Предмет"

    from backend.config import get_today
    today = get_today()

    dates, is_sched = await get_upcoming_or_fallback_dates(
        db_session, subject_id, from_date=today + timedelta(days=1), limit=4
    )
    default_d = dates[0] if dates else (today + timedelta(days=1))

    await state.update_data(
        subject_id=subject_id,
        due_date=default_d.isoformat(),
        assigned_date=today.isoformat(),
        attachments=[],
        description=""
    )
    await state.set_state(AddHomeworkStates.entering_content)

    d_name = DAYS_RU.get(default_d.isoweekday(), "")
    sched_hint = " *(следующий урок)*" if is_sched else ""
    text = (
        f"📚 **Добавление ДЗ — {subj_name}**\n\n"
        f"📅 **Дата сдачи по умолчанию:**\n"
        f"👉 **{d_name}, {default_d.strftime('%d.%m.%Y')}**{sched_hint}\n\n"
        "✍️ **Отправьте задание в чат:**\n"
        "• Текстом (номера упражнений, параграфы)\n"
        "• Либо фото/документами (можно отправить сразу несколько файлов!)\n\n"
        "*(Если нужно задать на другой день — выберите дату кнопками ниже)*:"
    )

    kb = build_date_keyboard(dates, selected_date=default_d, is_scheduled=is_sched)

    if isinstance(target_msg, CallbackQuery):
        await safe_edit_text(target_msg.message, text, reply_markup=kb)
        try:
            await target_msg.answer()
        except Exception:
            pass
    else:
        await safe_answer(target_msg, text, reply_markup=kb)


# ==================== ADD HOMEWORK WIZARD ====================

@router.callback_query(F.data == "admin_add_hw")
async def cb_start_add_hw(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    subjects = await get_all_subjects(db_session)
    kb = build_subjects_keyboard_grid(subjects)

    await state.set_state(AddHomeworkStates.choosing_subject)
    await safe_edit_text(
        callback.message,
        "📚 **Добавление ДЗ:**\n"
        "Выберите предмет кнопкой ниже или просто напишите его название в чат (например, *Русский*, *Алгебра*, *Физика*):",
        reply_markup=kb
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_hw_s_"))
async def cb_add_hw_subject_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    subj_id = int(callback.data.replace("adm_hw_s_", ""))
    await proceed_to_entering_content(callback, state, db_session, subj_id)


@router.message(AddHomeworkStates.choosing_subject)
async def msg_add_hw_subject_text(message: Message, state: FSMContext, db_session: AsyncSession):
    text = (message.text or "").strip()
    if not text:
        return

    subjects = await get_all_subjects(db_session)
    subj = find_subject_by_text(text, subjects)
    if subj:
        await proceed_to_entering_content(message, state, db_session, subj.id)
        return

    kb = build_subjects_keyboard_grid(subjects)
    await safe_answer(
        message,
        f"⚠️ Предмет *«{escape_md(text)}»* не найден в списке.\n\n"
        "Пожалуйста, выберите предмет кнопкой ниже или напишите одно из названий (например, *Русский*, *Алгебра*, *Литература*):",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("adm_hw_d_"))
async def cb_add_hw_date_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    target_d_str = callback.data.replace("adm_hw_d_", "")
    target_d = date.fromisoformat(target_d_str)
    await state.update_data(due_date=target_d.isoformat())

    data = await state.get_data()
    subj_id = data.get("subject_id", 0)
    subj = await get_subject_by_id(db_session, subj_id)
    subj_name = subj.name if subj else "Предмет"

    from backend.config import get_today
    today = get_today()
    dates, is_sched = await get_upcoming_or_fallback_dates(
        db_session, subj_id, from_date=today + timedelta(days=1), limit=4
    )

    if target_d not in dates:
        dates = [target_d] + [d for d in dates if d != target_d][:3]
        dates.sort()

    kb = build_date_keyboard(dates, selected_date=target_d, is_scheduled=is_sched)
    d_name = DAYS_RU.get(target_d.isoweekday(), "")
    text = (
        f"📚 **Добавление ДЗ — {subj_name}**\n\n"
        f"📅 **Выбранная дата сдачи:**\n"
        f"👉 **{d_name}, {target_d.strftime('%d.%m.%Y')}**\n\n"
        "✍️ **Отправьте задание в чат:**\n"
        "• Текстом (номера упражнений, параграфы)\n"
        "• Либо сразу фото или документ с подписью!"
    )

    await safe_edit_text(callback.message, text, reply_markup=kb)
    try:
        await callback.answer(f"Выбрана дата: {target_d.strftime('%d.%m.%Y')}")
    except Exception:
        pass


@router.callback_query(F.data == "adm_hw_open_cal")
async def cb_add_hw_open_cal(callback: CallbackQuery, state: FSMContext):
    from backend.config import get_today
    today = get_today()
    kb = get_inline_calendar("adm_hw", year=today.year, month=today.month, back_callback="admin_cancel")
    await state.set_state(AddHomeworkStates.entering_date)
    await safe_edit_text(
        callback.message,
        "📅 **Выберите дату на календаре для сдачи ДЗ:**",
        reply_markup=kb
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_nav_adm_hw_"))
async def cb_cal_nav_adm_hw(callback: CallbackQuery):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    kb = get_inline_calendar("adm_hw", year=year, month=month, back_callback="admin_cancel")
    await safe_edit_text(
        callback.message,
        "📅 **Выберите дату на календаре для сдачи ДЗ:**",
        reply_markup=kb
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_act_adm_hw_"))
async def cb_cal_act_adm_hw(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    day = int(parts[6])
    due_d = date(year, month, day)

    await state.update_data(due_date=due_d.isoformat())
    await state.set_state(AddHomeworkStates.entering_content)

    data = await state.get_data()
    subj = await get_subject_by_id(db_session, data.get("subject_id", 0))
    subj_name = subj.name if subj else "Предмет"
    day_ru = DAYS_RU.get(due_d.isoweekday(), "")

    await safe_edit_text(
        callback.message,
        f"📚 **Добавление ДЗ — {subj_name}**\n\n"
        f"📅 **Выбранная дата сдачи:**\n"
        f"👉 **{day_ru}, {due_d.strftime('%d.%m.%Y')}**\n\n"
        "✍️ **Отправьте задание в чат одним сообщением:**\n"
        "• Текстом (номера, параграфы)\n"
        "• Либо фото, документом (PDF, Word) или файлом с подписью!",
        reply_markup=get_cancel_keyboard()
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(AddHomeworkStates.entering_date)
async def msg_add_hw_date_text(message: Message, state: FSMContext, db_session: AsyncSession):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        await state.update_data(due_date=dt.isoformat())
        await state.set_state(AddHomeworkStates.entering_content)
        data = await state.get_data()
        subj = await get_subject_by_id(db_session, data.get("subject_id", 0))
        subj_name = subj.name if subj else "Предмет"
        day_ru = DAYS_RU.get(dt.isoweekday(), "")
        await safe_answer(
            message,
            f"📚 **Добавление ДЗ — {subj_name}**\n\n"
            f"📅 **Выбранная дата сдачи:**\n"
            f"👉 **{day_ru}, {dt.strftime('%d.%m.%Y')}**\n\n"
            "✍️ **Отправьте задание в чат одним сообщением:**\n"
            "• Текстом (номера, параграфы)\n"
            "• Либо фото, документом (PDF, Word) или файлом с подписью!",
            reply_markup=get_cancel_keyboard()
        )
    except ValueError:
        await safe_answer(message, "⚠️ Неверный формат даты. Выберите день на календаре или введите дату как `ДД.ММ.ГГГГ`:")


@router.message(AddHomeworkStates.entering_content)
async def msg_add_hw_collect_content(message: Message, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    attachments = list(data.get("attachments", []))
    description = data.get("description", "")

    if message.photo:
        photo = message.photo[-1]
        attachments.append({"type": "photo", "file_id": photo.file_id})
        if message.caption and not description:
            description = message.caption.strip()
    elif message.document:
        attachments.append({
            "type": "document",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name or "документ"
        })
        if message.caption and not description:
            description = message.caption.strip()
    elif message.video:
        attachments.append({
            "type": "document",
            "file_id": message.video.file_id,
            "file_name": message.video.file_name or "видео.mp4"
        })
        if message.caption and not description:
            description = message.caption.strip()
    elif message.audio:
        attachments.append({
            "type": "document",
            "file_id": message.audio.file_id,
            "file_name": message.audio.file_name or "аудио.mp3"
        })
        if message.caption and not description:
            description = message.caption.strip()
    elif message.text:
        description = message.text.strip()

    await state.update_data(attachments=attachments, description=description)

    # Дебаунс для медиа-групп (альбомов)
    if message.media_group_id:
        req_token = f"{message.media_group_id}_{time.time()}"
        await state.update_data(last_mg_req=req_token)
        await asyncio.sleep(0.4)
        latest_data = await state.get_data()
        if latest_data.get("last_mg_req") != req_token:
            return
        attachments = list(latest_data.get("attachments", []))
        description = latest_data.get("description", "")

    num_att = len(attachments)
    photos_cnt = len([a for a in attachments if a.get("type") == "photo"])
    docs_cnt = len([a for a in attachments if a.get("type") == "document"])

    if num_att > 0:
        details = []
        if photos_cnt > 0:
            details.append(f"📷 {photos_cnt} фото")
        if docs_cnt > 0:
            details.append(f"📄 {docs_cnt} файл(ов)")
        att_str = f"📎 **Прикреплено файлов:** {num_att} ({', '.join(details)})"
        save_btn_label = f"💾 Сохранить ДЗ ({num_att} влож.)"
    else:
        att_str = "📎 Вложений нет (можно отправить фото/документы/файлы)"
        save_btn_label = "💾 Сохранить ДЗ"

    desc_escaped = escape_md(description)
    desc_line = f"📝 **Текст задания:** {desc_escaped}" if description else "📝 **Текст:** _(не указан, можно отправить сейчас)_"

    due_d_str = data.get("due_date")
    from backend.config import get_today
    today = get_today()
    due_d = date.fromisoformat(due_d_str) if due_d_str else (today + timedelta(days=1))
    day_ru = DAYS_RU.get(due_d.isoweekday(), "")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=save_btn_label, callback_data="adm_hw_save_now")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )

    last_msg_id = data.get("hw_prompt_msg_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    text_msg = (
        f"📥 **Материалы получены!**\n\n"
        f"📅 **Дата сдачи:** {day_ru}, {due_d.strftime('%d.%m.%Y')}\n"
        f"{att_str}\n"
        f"{desc_line}\n\n"
        "⬇️ **Отправьте ещё фото/файлы или текст**, либо нажмите кнопку сохранения:"
    )

    sent = await safe_answer(message, text_msg, reply_markup=kb)
    if sent:
        await state.update_data(hw_prompt_msg_id=sent.message_id)


@router.callback_query(F.data == "adm_hw_save_now")
async def cb_add_hw_save_now(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    from backend.config import get_today
    today = get_today()

    due_d_str = data.get("due_date") or (today + timedelta(days=1)).isoformat()
    due_d = date.fromisoformat(due_d_str)

    assigned_d_str = data.get("assigned_date") or today.isoformat()
    assigned_d = date.fromisoformat(assigned_d_str)

    subj_id = data.get("subject_id")
    if not subj_id:
        await safe_edit_text(callback.message, "⚠️ Ошибка: предмет не выбран. Начните добавление ДЗ заново.", reply_markup=get_admin_panel_keyboard())
        await state.clear()
        return

    attachments = list(data.get("attachments", []))
    description = (data.get("description") or "").strip()

    if not description:
        if attachments:
            description = "Домашнее задание (см. прикрепленные материалы)"
        else:
            description = "Домашнее задание"

    hw = await create_homework(
        session=db_session,
        subject_id=subj_id,
        due_date=due_d,
        assigned_date=assigned_d,
        description=description,
        attachments=attachments,
        created_by=callback.from_user.id
    )

    subj = await get_subject_by_id(db_session, subj_id)
    subj_name = subj.name if subj else "Предмет"
    day_ru = DAYS_RU.get(due_d.isoweekday(), "")

    att_info = ""
    if attachments:
        photos = len([a for a in attachments if a.get("type") == "photo"])
        docs = len([a for a in attachments if a.get("type") == "document"])
        details = []
        if photos: details.append(f"{photos} фото")
        if docs: details.append(f"{docs} файл(ов)")
        att_info = f"📎 **Вложения ({len(attachments)}):** {', '.join(details)}\n"

    desc_escaped = escape_md(hw.description)
    await state.clear()
    await safe_edit_text(
        callback.message,
        f"✅ **Домашнее задание успешно сохранено!**\n\n"
        f"📖 **Предмет:** {subj_name}\n"
        f"📅 **Дата сдачи:** {day_ru}, {due_d.strftime('%d.%m.%Y')}\n"
        f"{att_info}"
        f"📝 **Задание:** {desc_escaped}\n\n"
        "📢 **Отправить оповещение ученикам о новом задании?**\n"
        "Выберите, куда сделать рассылку:",
        reply_markup=get_hw_notify_keyboard(hw.id)
    )
    try:
        await callback.answer("ДЗ успешно сохранено!")
    except Exception:
        pass


# ==================== HOMEWORK NOTIFICATIONS & DELETION ====================

@router.callback_query(F.data.startswith("adm_hwnotif_grp_"))
async def cb_hw_notif_group(callback: CallbackQuery, db_session: AsyncSession, bot: Bot):
    hw_id = int(callback.data.replace("adm_hwnotif_grp_", ""))
    hw = await get_homework_by_id(db_session, hw_id)
    if not hw:
        await callback.answer("ДЗ не найдено", show_alert=True)
        return

    g_cnt, _ = await send_new_homework_alert(bot, db_session, hw, to_group=True, to_users=False)
    await safe_edit_text(
        callback.message,
        f"📢 **Оповещение о новом ДЗ успешно отправлено в беседы класса ({g_cnt} чат(ов))!**",
        reply_markup=get_admin_panel_keyboard()
    )
    try:
        await callback.answer("Оповещение отправлено в беседу!")
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_hwnotif_all_"))
async def cb_hw_notif_all(callback: CallbackQuery, db_session: AsyncSession, bot: Bot):
    hw_id = int(callback.data.replace("adm_hwnotif_all_", ""))
    hw = await get_homework_by_id(db_session, hw_id)
    if not hw:
        await callback.answer("ДЗ не найдено", show_alert=True)
        return

    g_cnt, u_cnt = await send_new_homework_alert(bot, db_session, hw, to_group=True, to_users=True)
    await safe_edit_text(
        callback.message,
        f"📢 **Оповещение о новом ДЗ успешно разослано:**\n\n"
        f"• В беседы класса: **{g_cnt}**\n"
        f"• Ученикам в личные сообщения: **{u_cnt}**",
        reply_markup=get_admin_panel_keyboard()
    )
    try:
        await callback.answer("Оповещение разослано в беседу и всем в ЛС!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_hwnotif_none")
async def cb_hw_notif_none(callback: CallbackQuery):
    await safe_edit_text(
        callback.message,
        "✅ **Домашнее задание сохранено без рассылки.**",
        reply_markup=get_admin_panel_keyboard()
    )
    try:
        await callback.answer("Сохранено без оповещения")
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_hw_del_"))
async def cb_hw_delete(callback: CallbackQuery, db_session: AsyncSession):
    hw_id = int(callback.data.replace("adm_hw_del_", ""))
    deleted = await delete_homework(db_session, hw_id)
    if deleted:
        await safe_edit_text(
            callback.message,
            "🗑 **Домашнее задание успешно удалено!**",
            reply_markup=get_admin_panel_keyboard()
        )
        try:
            await callback.answer("ДЗ удалено!")
        except Exception:
            pass
    else:
        await callback.answer("Задание уже было удалено.", show_alert=True)


@router.callback_query(F.data == "admin_delete_hw")
async def cb_start_delete_hw(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    recent = await get_recent_active_homeworks(db_session)
    if not recent:
        await safe_edit_text(
            callback.message,
            "ℹ️ **Список актуальных ДЗ пуст.** Нет заданий для удаления.",
            reply_markup=get_admin_panel_keyboard()
        )
        try:
            await callback.answer()
        except Exception:
            pass
        return

    buttons = []
    for hw in recent:
        s_name = hw.subject.name if hw.subject else "Предмет"
        d_str = hw.due_date.strftime("%d.%m")
        desc_short = (hw.description[:25] + "...") if len(hw.description) > 25 else hw.description
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {s_name} ({d_str}): {desc_short}",
                callback_data=f"adm_hw_confirm_del_{hw.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад в панель", callback_data="admin_menu_back")])

    await safe_edit_text(
        callback.message,
        "🗑 **Удаление домашнего задания:**\n"
        "Выберите задание, которое хотите удалить:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_hw_confirm_del_"))
async def cb_confirm_delete_hw(callback: CallbackQuery, db_session: AsyncSession):
    hw_id = int(callback.data.replace("adm_hw_confirm_del_", ""))
    hw = await get_homework_by_id(db_session, hw_id)
    if not hw:
        await callback.answer("ДЗ уже удалено", show_alert=True)
        return

    s_name = hw.subject.name if hw.subject else "Предмет"
    d_str = hw.due_date.strftime("%d.%m.%Y")
    desc_escaped = escape_md(hw.description)
    text = (
        f"⚠️ **Вы уверены, что хотите удалить это ДЗ?**\n\n"
        f"📖 **Предмет:** {s_name}\n"
        f"📅 **Дата сдачи:** {d_str}\n"
        f"📝 **Задание:** {desc_escaped}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"adm_hw_del_{hw.id}")],
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_delete_hw")]
        ]
    )
    await safe_edit_text(callback.message, text, reply_markup=kb)
    try:
        await callback.answer()
    except Exception:
        pass
