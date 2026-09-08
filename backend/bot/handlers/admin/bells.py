import re
from datetime import date
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User
from backend.db.crud import (
    get_bell_schedule, get_bell_schedule_for_date, set_bell_schedule_item,
    set_bell_break_duration, clear_date_bells, save_bulk_date_bells
)
from backend.bot.keyboards.admin_kb import get_admin_panel_keyboard, get_cancel_keyboard
from backend.bot.keyboards.calendar import get_inline_calendar
from backend.bot.services.notifier import send_schedule_change_alert
from backend.bot.handlers.schedule import DAYS_RU
from backend.bot.handlers.admin.helpers import is_admin, parse_bells_text
from backend.bot.handlers.admin.states import EditBellStates, EditDateBellStates, EditBreakStates, BellWizardStates

router = Router(name="admin_bells_router")


# ==================== MAIN BELLS MENU ====================

@router.callback_query(F.data == "admin_edit_bells")
async def cb_bells_menu(callback: CallbackQuery, db_session: AsyncSession, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    bells = await get_bell_schedule(db_session)
    bell_text = "\n".join([
        f"• **{b.lesson_number} урок:** `{b.start_time}—{b.end_time}` (перемена {b.break_duration} мин)"
        for b in bells
    ]) if bells else "Расписание звонков не заполнено"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎛 Пошаговый конструктор звонков (кнопками)", callback_data="adm_bell_wizard")
            ],
            [
                InlineKeyboardButton(text="⚡ Изменить перемены", callback_data="adm_quick_breaks"),
                InlineKeyboardButton(text="⏰ Изменить время уроков", callback_data="adm_edit_bell_times")
            ],
            [
                InlineKeyboardButton(text="📅 Звонки на дату (сокращенные)", callback_data="adm_date_bells")
            ],
            [InlineKeyboardButton(text="🔙 В меню", callback_data="admin_menu_back")]
        ]
    )

    await callback.message.edit_text(
        f"🔔 **Текущее расписание звонков:**\n\n"
        f"{bell_text}\n\n"
        "Выберите, что хотите настроить:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


# ==================== QUICK BREAKS ====================

@router.callback_query(F.data == "adm_quick_breaks")
async def cb_quick_breaks_lesson_pick(callback: CallbackQuery, state: FSMContext):
    btns = [
        [InlineKeyboardButton(text=f"После {i} урока", callback_data=f"adm_brk_l_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(text=f"После {i} урока", callback_data=f"adm_brk_l_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_bells")]
    ]
    await state.set_state(EditBreakStates.choosing_lesson)
    await callback.message.edit_text(
        "⚡ **Быстрая настройка перемен:**\n\nПосле какого урока изменить длительность перемены?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_brk_l_"))
async def cb_quick_breaks_duration_pick(callback: CallbackQuery, state: FSMContext):
    l_num = int(callback.data.replace("adm_brk_l_", ""))
    await state.update_data(break_lesson=l_num)

    durations = [5, 10, 15, 20, 25, 30]
    btns = [
        [InlineKeyboardButton(text=f"{d} мин", callback_data=f"adm_brk_d_{d}") for d in durations[:3]],
        [InlineKeyboardButton(text=f"{d} мин", callback_data=f"adm_brk_d_{d}") for d in durations[3:]],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="adm_quick_breaks")]
    ]

    await state.set_state(EditBreakStates.choosing_duration)
    await callback.message.edit_text(
        f"⏳ **Выберите длительность перемены после {l_num}-го урока:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_brk_d_"))
async def cb_save_quick_break(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    duration = int(callback.data.replace("adm_brk_d_", ""))
    data = await state.get_data()
    l_num = data.get("break_lesson", 1)

    await set_bell_break_duration(db_session, lesson_number=l_num, break_duration=duration)
    await state.clear()

    bells = await get_bell_schedule(db_session)
    bell_lines = [
        f"• **{b.lesson_number} урок:** `{b.start_time}—{b.end_time}` (перемена {b.break_duration} мин)"
        for b in bells
    ] if bells else []

    await callback.message.edit_text(
        f"✅ Перемена после {l_num}-го урока установлена на **{duration} минут**!\n\n"
        f"⏰ **Расписание звонков автоматически пересчитано:**\n"
        + "\n".join(bell_lines),
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Пересчитано и сохранено!")
    except Exception:
        pass


# ==================== INDIVIDUAL BELL TIMES ====================

@router.callback_query(F.data == "adm_edit_bell_times")
async def cb_start_edit_bells(callback: CallbackQuery, state: FSMContext, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    btns = [
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_b_l_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_b_l_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="admin_menu_back")]
    ]

    await state.set_state(EditBellStates.choosing_lesson)
    await callback.message.edit_text(
        "🔔 **Редактор времени звонков:**\n\nВыберите номер урока:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_b_l_"))
async def cb_edit_bell_chosen(callback: CallbackQuery, state: FSMContext):
    l_num = int(callback.data.replace("adm_b_l_", ""))
    await state.update_data(bell_lesson=l_num)

    await state.set_state(EditBellStates.entering_times)
    await callback.message.edit_text(
        f"🔔 **Настройка времени для {l_num}-го урока:**\n\n"
        "Введите время начала, конца и перемены через пробел или дефис.\n"
        "**Пример:** `08:30-09:15 15` *(где 15 — перемена в минутах)*",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(EditBellStates.entering_times)
async def msg_edit_bell_save(message: Message, state: FSMContext, db_session: AsyncSession):
    text = message.text.strip()
    match = re.match(r"(\d{1,2}:\d{2})\s*[-—–]\s*(\d{1,2}:\d{2})(?:\s+(\d+))?", text)
    if not match:
        await message.answer("⚠️ Неверный формат. Введите время как: `08:30-09:15 15`:")
        return

    start_t, end_t, brk = match.groups()
    break_duration = int(brk) if brk else 10

    data = await state.get_data()
    l_num = data["bell_lesson"]

    await set_bell_schedule_item(
        session=db_session,
        lesson_number=l_num,
        start_time=start_t,
        end_time=end_t,
        break_duration=break_duration
    )

    await state.clear()
    await message.answer(
        f"✅ **Звонки для {l_num}-го урока обновлены!**\n\n"
        f"⏰ `{start_t} — {end_t}` (перемена {break_duration} мин)",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )


# ==================== DATE-SPECIFIC BELLS ====================

@router.callback_query(F.data == "adm_date_bells")
async def cb_admin_date_bells(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from backend.config import get_today
    today = get_today()
    kb = get_inline_calendar("adm_dtb", year=today.year, month=today.month, back_callback="admin_edit_bells")
    await callback.message.edit_text(
        "📅 **Расписание звонков на определенный день**\n\n"
        "Выберите дату в календаре, для которой нужно настроить особое расписание звонков (например, сокращенные уроки):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_nav_adm_dtb_"))
async def cb_cal_nav_adm_dtb(callback: CallbackQuery):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    kb = get_inline_calendar("adm_dtb", year=year, month=month, back_callback="admin_edit_bells")
    await callback.message.edit_text(
        "📅 **Расписание звонков на определенный день**\n\n"
        "Выберите дату в календаре:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_act_adm_dtb_"))
async def cb_cal_act_adm_dtb(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    day = int(parts[6])
    target_d = date(year, month, day)

    await state.update_data(edit_bell_target_date=target_d.isoformat())
    await state.set_state(EditDateBellStates.choosing_date)

    day_name = DAYS_RU.get(target_d.isoweekday(), "День")
    bells = await get_bell_schedule_for_date(db_session, target_d)

    bell_lines = []
    for b in bells:
        brk = f" *(перемена {b.break_duration} мин)*" if b.break_duration else ""
        bell_lines.append(f"• **{b.lesson_number} урок:** `{b.start_time}—{b.end_time}`{brk}")

    text = (
        f"📅 **Звонки на {day_name} ({target_d.strftime('%d.%m.%Y')}):**\n\n"
        + "\n".join(bell_lines) + "\n\n"
        "Выберите готовый шаблон или введите свое расписание звонков:"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎛 Пошаговый конструктор (кнопками)", callback_data="adm_dtb_wizard")],
            [InlineKeyboardButton(text="⚡ Сокращенные уроки (по 35 мин)", callback_data="adm_dtb_p35")],
            [InlineKeyboardButton(text="⚡ Сокращенные уроки (по 30 мин)", callback_data="adm_dtb_p30")],
            [InlineKeyboardButton(text="✏️ Ввести звонки текстом (свободно)", callback_data="adm_dtb_bulk")],
            [InlineKeyboardButton(text="🗑 Сбросить (к стандартным)", callback_data="adm_dtb_reset")],
            [InlineKeyboardButton(text="🔙 К выбору даты", callback_data="adm_date_bells")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_dtb_p35")
async def cb_dtb_preset_35(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    target_d_str = data.get("edit_bell_target_date")
    if not target_d_str:
        await callback.answer("Выберите дату заново", show_alert=True)
        return
    target_d = date.fromisoformat(target_d_str)
    day_name = DAYS_RU.get(target_d.isoweekday(), "День")

    p35 = [
        (1, "08:30", "09:05", 10),
        (2, "09:15", "09:50", 10),
        (3, "10:00", "10:35", 15),
        (4, "10:50", "11:25", 10),
        (5, "11:35", "12:10", 10),
        (6, "12:20", "12:55", 10),
        (7, "13:05", "13:40", 5),
        (8, "13:45", "14:20", 0),
    ]

    await save_bulk_date_bells(db_session, target_d, p35)

    bell_lines = [f"{n} урок: {s} – {e}" for n, s, e, _ in p35]
    await state.update_data(
        alert_title=f"🔔 **Сокращенные звонки (по 35 мин) на {day_name} ({target_d.strftime('%d.%m.%Y')}):**",
        alert_lines=bell_lines
    )
    await state.set_state(EditDateBellStates.confirm_notification)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Да, оповестить класс!", callback_data="adm_dtb_notify_yes"),
                InlineKeyboardButton(text="🔇 Без оповещения", callback_data="adm_dtb_notify_no")
            ]
        ]
    )

    await callback.message.edit_text(
        f"✅ **Установлены сокращенные уроки по 35 минут на {target_d.strftime('%d.%m.%Y')}!**\n\n"
        "📢 **Разослать оповещение классу об изменении звонков?**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сохранено!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_dtb_p30")
async def cb_dtb_preset_30(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    target_d_str = data.get("edit_bell_target_date")
    if not target_d_str:
        await callback.answer("Выберите дату заново", show_alert=True)
        return
    target_d = date.fromisoformat(target_d_str)
    day_name = DAYS_RU.get(target_d.isoweekday(), "День")

    p30 = [
        (1, "08:30", "09:00", 10),
        (2, "09:10", "09:40", 10),
        (3, "09:50", "10:20", 10),
        (4, "10:30", "11:00", 10),
        (5, "11:10", "11:40", 10),
        (6, "11:50", "12:20", 10),
        (7, "12:30", "13:00", 5),
        (8, "13:05", "13:35", 0),
    ]

    await save_bulk_date_bells(db_session, target_d, p30)

    bell_lines = [f"{n} урок: {s} – {e}" for n, s, e, _ in p30]
    await state.update_data(
        alert_title=f"🔔 **Сокращенные звонки (по 30 мин) на {day_name} ({target_d.strftime('%d.%m.%Y')}):**",
        alert_lines=bell_lines
    )
    await state.set_state(EditDateBellStates.confirm_notification)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Да, оповестить класс!", callback_data="adm_dtb_notify_yes"),
                InlineKeyboardButton(text="🔇 Без оповещения", callback_data="adm_dtb_notify_no")
            ]
        ]
    )

    await callback.message.edit_text(
        f"✅ **Установлены сокращенные уроки по 30 минут на {target_d.strftime('%d.%m.%Y')}!**\n\n"
        "📢 **Разослать оповещение классу об изменении звонков?**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сохранено!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_dtb_bulk")
async def cb_dtb_bulk_prompt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_d_str = data.get("edit_bell_target_date")
    if not target_d_str:
        await callback.answer("Выберите дату заново", show_alert=True)
        return
    target_d = date.fromisoformat(target_d_str)
    day_name = DAYS_RU.get(target_d.isoweekday(), "День")

    await state.set_state(EditDateBellStates.entering_text_bulk)
    await callback.message.edit_text(
        f"✏️ **Введите расписание звонков на {day_name} ({target_d.strftime('%d.%m.%Y')}):**\n\n"
        "Формат свободный — с номерами уроков или без, построчно или через запятую, например:\n"
        "```text\n"
        "1. 08:30 - 09:05\n"
        "2. 09:15 - 09:50\n"
        "3. 10:00 - 10:35\n"
        "4. 10:45 - 11:20\n"
        "```\n"
        "_(Перемены между уроками рассчитаются автоматически)_",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(EditDateBellStates.entering_text_bulk)
async def msg_dtb_bulk_save(message: Message, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    target_d = date.fromisoformat(data["edit_bell_target_date"])
    day_name = DAYS_RU.get(target_d.isoweekday(), "День")

    parsed = parse_bells_text(message.text)
    if not parsed:
        await message.answer(
            "⚠️ Не удалось распознать время уроков. Пожалуйста, укажите время уроков (например, `08:30 - 09:10`):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
        return

    await save_bulk_date_bells(db_session, target_d, parsed)

    bell_lines = [f"{l_num} урок: {s} – {e} (перемена {b} мин)" for l_num, s, e, b in parsed]
    await state.update_data(
        alert_title=f"🔔 **Новое расписание звонков на {day_name} ({target_d.strftime('%d.%m.%Y')}):**",
        alert_lines=bell_lines
    )
    await state.set_state(EditDateBellStates.confirm_notification)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Да, оповестить класс!", callback_data="adm_dtb_notify_yes"),
                InlineKeyboardButton(text="🔇 Без оповещения", callback_data="adm_dtb_notify_no")
            ]
        ]
    )

    await message.answer(
        f"✅ **Расписание звонков на {target_d.strftime('%d.%m.%Y')} сохранено ({len(parsed)} ур.)!**\n\n"
        + "\n".join(bell_lines) + "\n\n"
        "📢 **Разослать оповещение классу об изменении звонков?**",
        reply_markup=kb,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "adm_dtb_reset")
async def cb_dtb_reset(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    target_d_str = data.get("edit_bell_target_date")
    if not target_d_str:
        await callback.answer("Выберите дату заново", show_alert=True)
        return
    target_d = date.fromisoformat(target_d_str)
    day_name = DAYS_RU.get(target_d.isoweekday(), "День")

    await clear_date_bells(db_session, target_d)

    perm_bells = await get_bell_schedule(db_session)
    bell_lines = [f"{b.lesson_number} урок: {b.start_time} – {b.end_time}" for b in perm_bells]

    await state.update_data(
        alert_title=f"🔔 **{day_name} ({target_d.strftime('%d.%m.%Y')}):**\n_(Расписание звонков возвращено к стандартному)_",
        alert_lines=bell_lines
    )
    await state.set_state(EditDateBellStates.confirm_notification)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Да, оповестить класс!", callback_data="adm_dtb_notify_yes"),
                InlineKeyboardButton(text="🔇 Без оповещения", callback_data="adm_dtb_notify_no")
            ]
        ]
    )

    await callback.message.edit_text(
        f"🗑 **Расписание звонков на {target_d.strftime('%d.%m.%Y')} сброшено к стандартному!**\n\n"
        "📢 **Оповестить класс о возврате к стандартным звонкам?**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сброшено!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_dtb_notify_yes")
async def cb_dtb_notify_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    title = data.get("alert_title", "Изменение расписания звонков")
    lines = data.get("alert_lines", [])

    await send_schedule_change_alert(bot, title, lines)
    await state.clear()
    await callback.message.edit_text(
        "📢 **Оповещение об изменении звонков успешно разослано классу!**",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Разослано!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_dtb_notify_no")
async def cb_dtb_notify_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔇 **Изменения сохранены без рассылки оповещения.**",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сохранено!")
    except Exception:
        pass


# ==================== STEP-BY-STEP BELL WIZARD ====================

@router.callback_query(F.data == "adm_bell_wizard")
async def cb_bell_wizard_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BellWizardStates.choosing_target)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗓 Стандартные звонки (на весь год)", callback_data="wiz_b_tgt_perm")],
            [InlineKeyboardButton(text="📅 Звонки на дату (сокращенные/особые)", callback_data="wiz_b_tgt_date")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_bells")]
        ]
    )
    await callback.message.edit_text(
        "🎛 **Пошаговый конструктор звонков (кнопками)**\n\n"
        "Для чего вы хотите настроить звонки?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_dtb_wizard")
async def cb_bell_wizard_start_from_date(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_d_str = data.get("edit_bell_target_date")
    await state.update_data(bell_target_mode="date", bell_target_date=target_d_str)
    await state.set_state(BellWizardStates.choosing_count)
    await show_bell_wizard_count(callback)
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "wiz_b_tgt_perm")
async def cb_bell_target_perm(callback: CallbackQuery, state: FSMContext):
    await state.update_data(bell_target_mode="perm")
    await state.set_state(BellWizardStates.choosing_count)
    await show_bell_wizard_count(callback)
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "wiz_b_tgt_date")
async def cb_bell_target_date_pick(callback: CallbackQuery, state: FSMContext):
    from backend.config import get_today
    today = get_today()
    kb = get_inline_calendar("wiz_bd", year=today.year, month=today.month, back_callback="adm_bell_wizard")
    await state.set_state(BellWizardStates.choosing_date)
    await callback.message.edit_text(
        "📅 **Выберите дату для настройки расписания звонков:**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_nav_wiz_bd_"))
async def cb_cal_nav_wiz_bd(callback: CallbackQuery):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    kb = get_inline_calendar("wiz_bd", year=year, month=month, back_callback="adm_bell_wizard")
    await callback.message.edit_text(
        "📅 **Выберите дату для настройки расписания звонков:**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_act_wiz_bd_"))
async def cb_cal_act_wiz_bd(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    day = int(parts[6])
    target_d = date(year, month, day)

    await state.update_data(bell_target_mode="date", bell_target_date=target_d.isoformat(), edit_bell_target_date=target_d.isoformat())
    await state.set_state(BellWizardStates.choosing_count)
    await show_bell_wizard_count(callback)
    try:
        await callback.answer()
    except Exception:
        pass


async def show_bell_wizard_count(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="5 уроков", callback_data="wiz_bc_5"), InlineKeyboardButton(text="6 уроков", callback_data="wiz_bc_6")],
            [InlineKeyboardButton(text="7 уроков", callback_data="wiz_bc_7"), InlineKeyboardButton(text="8 уроков", callback_data="wiz_bc_8")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )
    await callback.message.edit_text(
        "🎛 **Шаг 1: Количество уроков**\n\n"
        "Сколько уроков будет в расписании звонков?",
        reply_markup=kb,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("wiz_bc_"))
async def cb_bell_count_chosen(callback: CallbackQuery, state: FSMContext):
    cnt = int(callback.data.replace("wiz_bc_", ""))
    await state.update_data(bell_count=cnt)
    await state.set_state(BellWizardStates.choosing_start)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="08:00", callback_data="wiz_bs_08:00"), InlineKeyboardButton(text="08:15", callback_data="wiz_bs_08:15")],
            [InlineKeyboardButton(text="08:30 (стандарт)", callback_data="wiz_bs_08:30"), InlineKeyboardButton(text="09:00", callback_data="wiz_bs_09:00")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )
    await callback.message.edit_text(
        "🎛 **Шаг 2: Время начала 1-го урока**\n\n"
        "Во сколько начинается первый урок?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("wiz_bs_"))
async def cb_bell_start_chosen(callback: CallbackQuery, state: FSMContext):
    start_time = callback.data.replace("wiz_bs_", "")
    await state.update_data(bell_start=start_time)
    await state.set_state(BellWizardStates.choosing_duration)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="40 минут (Стандарт)", callback_data="wiz_bdur_40")],
            [InlineKeyboardButton(text="35 минут (Сокращенный)", callback_data="wiz_bdur_35")],
            [InlineKeyboardButton(text="30 минут (Сокращенный)", callback_data="wiz_bdur_30")],
            [InlineKeyboardButton(text="45 минут (Полный)", callback_data="wiz_bdur_45")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )
    await callback.message.edit_text(
        f"🎛 **Шаг 3: Длительность одного урока** (начало в {start_time})\n\n"
        "Сколько минут длится каждый урок?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("wiz_bdur_"))
async def cb_bell_duration_chosen(callback: CallbackQuery, state: FSMContext):
    dur = int(callback.data.replace("wiz_bdur_", ""))
    await state.update_data(bell_duration=dur)
    await state.set_state(BellWizardStates.choosing_break)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="10 минут (Стандарт)", callback_data="wiz_bbrk_10")],
            [InlineKeyboardButton(text="15 минут", callback_data="wiz_bbrk_15")],
            [InlineKeyboardButton(text="5 минут (Минимум)", callback_data="wiz_bbrk_5")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )
    await callback.message.edit_text(
        f"🎛 **Шаг 4: Длительность обычных перемен** (урок {dur} мин)\n\n"
        "Сколько минут длится стандартная перемена?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("wiz_bbrk_"))
async def cb_bell_break_chosen(callback: CallbackQuery, state: FSMContext):
    brk = int(callback.data.replace("wiz_bbrk_", ""))
    await state.update_data(bell_regular_break=brk)
    await state.set_state(BellWizardStates.choosing_lunch)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="15 мин после 2 и 3 урока (Стандарт 11Б)", callback_data="wiz_blunch_23_15")],
            [InlineKeyboardButton(text="15 мин после 3 урока", callback_data="wiz_blunch_3_15")],
            [InlineKeyboardButton(text="20 мин после 3 урока", callback_data="wiz_blunch_3_20")],
            [InlineKeyboardButton(text="Без большой перемены (все одинаковые)", callback_data="wiz_blunch_none")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )
    await callback.message.edit_text(
        "🎛 **Шаг 5: Большая перемена (на обед / столовую)**\n\n"
        "Нужна ли увеличенная перемена?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("wiz_blunch_"))
async def cb_bell_lunch_chosen(callback: CallbackQuery, state: FSMContext):
    lunch_scheme = callback.data.replace("wiz_blunch_", "")
    data = await state.get_data()

    count = data.get("bell_count", 7)
    start_str = data.get("bell_start", "08:30")
    lesson_dur = data.get("bell_duration", 40)
    reg_break = data.get("bell_regular_break", 10)

    cur_h, cur_m = map(int, start_str.split(":"))
    current_minutes = cur_h * 60 + cur_m

    generated_bells = []
    for l_num in range(1, count + 1):
        s_h, s_m = divmod(current_minutes, 60)
        end_minutes = current_minutes + lesson_dur
        e_h, e_m = divmod(end_minutes, 60)

        if l_num == count:
            brk = 0
        elif lunch_scheme == "23_15" and l_num in (2, 3):
            brk = 15
        elif lunch_scheme == "3_15" and l_num == 3:
            brk = 15
        elif lunch_scheme == "3_20" and l_num == 3:
            brk = 20
        elif l_num == count - 1 and reg_break >= 10:
            brk = 5
        else:
            brk = reg_break

        start_time_str = f"{s_h:02d}:{s_m:02d}"
        end_time_str = f"{e_h:02d}:{e_m:02d}"

        generated_bells.append((l_num, start_time_str, end_time_str, brk))
        current_minutes = end_minutes + brk

    await state.update_data(generated_bells=generated_bells)
    await state.set_state(BellWizardStates.confirm_save)

    lines = []
    for num, s, e, b in generated_bells:
        brk_str = f" *(перемена {b} мин)*" if b > 0 else ""
        lines.append(f"• **{num} урок:** `{s}—{e}`{brk_str}")

    target_mode = data.get("bell_target_mode", "perm")
    if target_mode == "perm":
        title = "🗓 **Стандартное расписание звонков (на весь год)**"
    else:
        t_date_str = data.get("bell_target_date") or date.today().isoformat()
        t_date = date.fromisoformat(t_date_str)
        title = f"📅 **Расписание звонков на {DAYS_RU.get(t_date.isoweekday(), '')} ({t_date.strftime('%d.%m.%Y')})**"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Применить и сохранить звонки", callback_data="wiz_b_save")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )

    await callback.message.edit_text(
        f"{title}\n\n"
        "🔔 **Сформированное расписание:**\n\n"
        + "\n".join(lines) + "\n\n"
        "Сохранить это расписание звонков?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "wiz_b_save")
async def cb_bell_wizard_save(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    bells = data["generated_bells"]
    target_mode = data.get("bell_target_mode", "perm")

    if target_mode == "perm":
        for l_num, s_t, e_t, brk in bells:
            await set_bell_schedule_item(
                session=db_session,
                lesson_number=l_num,
                start_time=s_t,
                end_time=e_t,
                break_duration=brk,
                specific_date=None
            )
        await state.clear()
        await callback.message.edit_text(
            f"✅ **Стандартное расписание звонков успешно сохранено ({len(bells)} уроков)!**",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="Markdown"
        )
    else:
        target_d = date.fromisoformat(data["bell_target_date"])
        await save_bulk_date_bells(db_session, target_d, bells)

        day_name = DAYS_RU.get(target_d.isoweekday(), "День")
        bell_lines = [f"{n} урок: {s} – {e}" for n, s, e, _ in bells]
        await state.update_data(
            alert_title=f"🔔 **Новые звонки на {day_name} ({target_d.strftime('%d.%m.%Y')}):**\n" + "\n".join(bell_lines),
            alert_lines=bell_lines
        )
        await state.set_state(EditDateBellStates.confirm_notification)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Да, оповестить класс!", callback_data="adm_dtb_notify_yes")],
                [InlineKeyboardButton(text="🔇 Без оповещения", callback_data="adm_dtb_notify_no")]
            ]
        )
        await callback.message.edit_text(
            f"✅ **Расписание звонков на {day_name} ({target_d.strftime('%d.%m.%Y')}) сохранено!**\n\n"
            "📢 **Разослать классу и в беседы уведомление об изменении звонков?**",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    try:
        await callback.answer("Звонки сохранены!")
    except Exception:
        pass
