from datetime import date
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User
from backend.db.crud import (
    get_all_subjects, get_subject_by_id,
    set_schedule_item, set_date_schedule_item, set_permanent_schedule_item,
    get_schedule_for_date, get_schedule_for_day,
    save_bulk_date_schedule, save_bulk_permanent_schedule, clear_date_schedule,
    auto_shift_active_homeworks, create_substitution,
    get_notifiable_users, get_approved_group_chats
)
from backend.bot.keyboards.admin_kb import (
    get_admin_panel_keyboard, get_cancel_keyboard, get_notify_confirm_keyboard,
    get_date_schedule_notify_keyboard
)
from backend.bot.keyboards.calendar import get_inline_calendar
from backend.bot.services.notifier import send_schedule_change_alert
from backend.bot.handlers.schedule import DAYS_RU
from backend.bot.handlers.admin.helpers import is_admin, parse_schedule_text
from backend.bot.handlers.admin.states import (
    EditScheduleStates, EditDateScheduleStates, AddSubstitutionStates, ScheduleWizardStates
)

router = Router(name="admin_schedule_router")


# ==================== PERMANENT SCHEDULE ====================

@router.callback_query(F.data == "admin_edit_schedule")
async def cb_start_edit_schedule(callback: CallbackQuery, state: FSMContext, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    days = [("Пн", 1), ("Вт", 2), ("Ср", 3), ("Чт", 4), ("Пт", 5), ("Сб", 6)]
    buttons = []
    current_row = []
    for d_name, d_num in days:
        current_row.append(InlineKeyboardButton(text=d_name, callback_data=f"adm_sc_day_{d_num}"))
        if len(current_row) == 3:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="admin_menu_back")])

    await state.set_state(EditScheduleStates.choosing_day)
    await callback.message.edit_text(
        "📅 **Редактор расписания уроков:**\n\nВыберите день недели для настройки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_sc_day_"))
async def cb_edit_sched_day_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    day_num = int(callback.data.replace("adm_sc_day_", ""))
    await state.update_data(edit_day=day_num)

    day_names = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}
    day_name = day_names.get(day_num, "День")

    items = await get_schedule_for_day(db_session, day_num)
    cur_lines = [f"{it.lesson_number}. {it.subject.name if it.subject else 'Урок'}" for it in items]
    cur_text = "\n".join(cur_lines) if cur_lines else "_Расписание пока не заполнено_"

    btns = [
        [InlineKeyboardButton(text="🎛 Пошаговый конструктор (кнопками)", callback_data="adm_sc_wizard")],
        [InlineKeyboardButton(text="✏️ Ввести весь день текстом (быстро)", callback_data="adm_sc_bulk")],
        [InlineKeyboardButton(text="🔢 Изменить отдельный урок", callback_data="adm_sc_single")],
        [InlineKeyboardButton(text="🔙 Назад к дням", callback_data="admin_edit_schedule")]
    ]

    try:
        await callback.message.edit_text(
            f"🗓 **Постоянное расписание — {day_name}:**\n\n"
            f"{cur_text}\n\n"
            "Выберите способ редактирования:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
            parse_mode="Markdown"
        )
    except Exception:
        pass
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_sc_bulk")
async def cb_edit_sched_bulk_prompt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    day_num = data.get("edit_day", 1)
    day_names = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}
    day_name = day_names.get(day_num, "день")

    await state.set_state(EditScheduleStates.entering_text_bulk)
    await callback.message.edit_text(
        f"✏️ **Введите постоянное расписание на {day_name} одним сообщением:**\n\n"
        "Каждый урок пишите с новой строки. Новые предметы добавятся автоматически.\n\n"
        "**Пример:**\n"
        "`1. Алгебра`\n"
        "`2. Русский язык`\n"
        "`3. Физика`\n"
        "`4. Химия`\n"
        "`5. Литература`\n"
        "`6. Физкультура`\n"
        "`7. Английский язык`\n\n"
        "Отправьте текст в ответ на это сообщение 👇",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(EditScheduleStates.entering_text_bulk)
async def msg_edit_sched_bulk_save(message: Message, state: FSMContext, db_session: AsyncSession):
    lessons = parse_schedule_text(message.text)
    if not lessons:
        await message.answer(
            "⚠️ Не удалось распознать уроки. Отправьте список уроков построчно:\n\n"
            "1. Алгебра\n2. Физика\n3. Русский язык"
        )
        return

    data = await state.get_data()
    day_num = data.get("edit_day", 1)
    day_names = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}
    day_name = day_names.get(day_num, "день")

    saved_items = await save_bulk_permanent_schedule(db_session, day_num, lessons)
    await auto_shift_active_homeworks(db_session)
    lines = [f"  {l_num}. {s_name}" for l_num, s_name in lessons]

    await state.clear()
    await message.answer(
        f"✅ **Постоянное расписание на {day_name} успешно сохранено ({len(saved_items)} ур.)!**\n\n" +
        "\n".join(lines),
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "adm_sc_single")
async def cb_edit_sched_single_lessons(callback: CallbackQuery, state: FSMContext):
    btns = [
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_sc_l_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_sc_l_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_schedule")]
    ]
    await state.set_state(EditScheduleStates.choosing_lesson)
    await callback.message.edit_text(
        "Какой по счету урок вы хотите изменить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_sc_l_"))
async def cb_edit_sched_lesson_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    l_num = int(callback.data.replace("adm_sc_l_", ""))
    await state.update_data(edit_lesson=l_num)

    subjects = await get_all_subjects(db_session)
    btns = [[InlineKeyboardButton(text=s.name, callback_data=f"adm_sc_subj_{s.id}")] for s in subjects]
    btns.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])

    await state.set_state(EditScheduleStates.choosing_subject)
    await callback.message.edit_text(
        f"📖 **Выберите предмет для {l_num}-го урока:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_sc_subj_"))
async def cb_edit_sched_save(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    subj_id = int(callback.data.replace("adm_sc_subj_", ""))
    data = await state.get_data()
    day_num = data["edit_day"]
    l_num = data["edit_lesson"]

    await set_permanent_schedule_item(
        session=db_session,
        day_of_week=day_num,
        lesson_number=l_num,
        subject_id=subj_id
    )
    await auto_shift_active_homeworks(db_session)

    subj = await get_subject_by_id(db_session, subj_id)
    day_names = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб"}

    await state.clear()
    await callback.message.edit_text(
        f"✅ **Постоянное расписание обновлено!**\n\n"
        f"📅 **День:** {day_names.get(day_num, '')}\n"
        f"🔢 **Урок:** {l_num}-й\n"
        f"📖 **Предмет:** {subj.name if subj else ''}",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сохранено!")
    except Exception:
        pass


# ==================== DATE-SPECIFIC SCHEDULE ====================

@router.callback_query(F.data == "admin_edit_date_schedule")
async def cb_start_edit_date_schedule(callback: CallbackQuery, state: FSMContext, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    today = date.today()
    kb = get_inline_calendar("adm_dtsched", year=today.year, month=today.month, back_callback="admin_menu_back")

    await state.set_state(EditDateScheduleStates.choosing_date)
    await callback.message.edit_text(
        "📅 **Расписание на конкретную дату:**\n\n"
        "Выберите дату в календаре для настройки уроков:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(EditDateScheduleStates.choosing_date, F.data.startswith("cal_nav_adm_dtsched_"))
async def cb_cal_nav_adm_dtsched(callback: CallbackQuery):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    kb = get_inline_calendar("adm_dtsched", year=year, month=month, back_callback="admin_menu_back")
    await callback.message.edit_text(
        "📅 **Расписание на конкретную дату:**\n\n"
        "Выберите дату в календаре для настройки уроков:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_act_adm_dtsched_"))
async def cb_cal_act_adm_dtsched(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    day = int(parts[6])
    target_d = date(year, month, day)

    await state.update_data(edit_target_date=target_d.isoformat())

    lessons = await get_schedule_for_date(db_session, target_d)
    lesson_lines = [f"{l.lesson_number}. {l.subject.name}" for l in lessons]
    lessons_str = "\n".join(lesson_lines) if lesson_lines else "_Уроки еще не назначены_"

    day_name = DAYS_RU.get(target_d.isoweekday(), "День")
    date_formatted = target_d.strftime("%d.%m.%Y")

    btns = [
        [InlineKeyboardButton(text="🎛 Пошаговый конструктор (кнопками)", callback_data="adm_dt_wizard")],
        [InlineKeyboardButton(text="✏️ Ввести весь день текстом (быстро)", callback_data="adm_dt_bulk")],
        [InlineKeyboardButton(text="🔢 Изменить отдельный урок", callback_data="adm_dt_single")],
        [InlineKeyboardButton(text="🗑 Сбросить (к постоянному)", callback_data="adm_dt_reset")],
        [InlineKeyboardButton(text="🔙 К выбору даты", callback_data="admin_edit_date_schedule")]
    ]

    await callback.message.edit_text(
        f"📅 **Расписание на {day_name} ({date_formatted}):**\n\n"
        f"{lessons_str}\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_dt_bulk")
async def cb_edit_dt_sched_bulk_prompt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_d_str = data.get("edit_target_date")
    if not target_d_str:
        await callback.answer("Выберите дату заново", show_alert=True)
        return
    target_d = date.fromisoformat(target_d_str)
    day_name = DAYS_RU.get(target_d.isoweekday(), "")

    await state.set_state(EditDateScheduleStates.entering_text_bulk)
    await callback.message.edit_text(
        f"✏️ **Введите расписание на {day_name} ({target_d.strftime('%d.%m.%Y')}) одним сообщением:**\n\n"
        "Каждый урок пишите с новой строки. Новые предметы создадутся автоматически.\n\n"
        "**Пример сообщения:**\n"
        "`1. География`\n"
        "`2. История`\n"
        "`3. Обществознание`\n"
        "`4. Английский язык`\n"
        "`5. Алгебра`\n"
        "`6. Физика`\n\n"
        "Отправьте текст в ответ на это сообщение 👇",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(EditDateScheduleStates.entering_text_bulk)
async def msg_edit_dt_sched_bulk_save(message: Message, state: FSMContext, db_session: AsyncSession):
    lessons = parse_schedule_text(message.text)
    if not lessons:
        await message.answer(
            "⚠️ Не удалось распознать уроки. Отправьте список уроков построчно:\n\n"
            "1. Алгебра\n2. Физика\n3. Русский язык"
        )
        return

    data = await state.get_data()
    target_d = date.fromisoformat(data["edit_target_date"])
    day_name = DAYS_RU.get(target_d.isoweekday(), "")

    saved_items = await save_bulk_date_schedule(db_session, target_d, lessons)
    await auto_shift_active_homeworks(db_session)
    schedule_lines = [f"{l_num}. {s_name}" for l_num, s_name in lessons]

    await state.update_data(
        alert_title=f"📅 **{day_name} ({target_d.strftime('%d.%m.%Y')}):**",
        alert_lines=schedule_lines
    )
    await state.set_state(EditDateScheduleStates.confirm_notification)

    await message.answer(
        f"✅ **Расписание на {day_name} ({target_d.strftime('%d.%m.%Y')}) сохранено ({len(saved_items)} ур.)!**\n\n" +
        "\n".join(schedule_lines) + "\n\n" +
        "📢 **Разослать оповещение классу об изменении расписания?**",
        reply_markup=get_date_schedule_notify_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "adm_dt_single")
async def cb_edit_dt_sched_single_pick(callback: CallbackQuery, state: FSMContext):
    btns = [
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_dt_l_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_dt_l_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(text="🔙 К выбору даты", callback_data="admin_edit_date_schedule")]
    ]
    await state.set_state(EditDateScheduleStates.choosing_lesson)
    await callback.message.edit_text(
        "Какой урок хотите назначить/изменить на эту дату?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_dt_l_"))
async def cb_edit_dt_sched_lesson_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    l_num = int(callback.data.replace("adm_dt_l_", ""))
    await state.update_data(edit_target_lesson=l_num)

    subjects = await get_all_subjects(db_session)
    btns = [[InlineKeyboardButton(text=s.name, callback_data=f"adm_dt_s_{s.id}")] for s in subjects]
    btns.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])

    await state.set_state(EditDateScheduleStates.choosing_subject)
    await callback.message.edit_text(
        f"📖 **Выберите предмет для {l_num}-го урока на эту дату:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_dt_s_"))
async def cb_edit_dt_sched_save(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    subj_id = int(callback.data.replace("adm_dt_s_", ""))
    data = await state.get_data()
    target_d = date.fromisoformat(data["edit_target_date"])
    l_num = data["edit_target_lesson"]

    await set_date_schedule_item(
        session=db_session,
        target_date=target_d,
        lesson_number=l_num,
        subject_id=subj_id
    )
    await auto_shift_active_homeworks(db_session)

    subj = await get_subject_by_id(db_session, subj_id)
    day_name = DAYS_RU.get(target_d.isoweekday(), "")

    lessons = await get_schedule_for_date(db_session, target_d)
    schedule_lines = [f"{l.lesson_number}. {l.subject.name}" for l in lessons]

    await state.update_data(
        alert_title=f"📅 **{day_name} ({target_d.strftime('%d.%m.%Y')}):**\n_(Изменен {l_num} урок: {subj.name if subj else ''})_",
        alert_lines=schedule_lines
    )
    await state.set_state(EditDateScheduleStates.confirm_notification)

    await callback.message.edit_text(
        f"✅ **Урок на дату сохранен!**\n\n"
        f"📅 **Дата:** {target_d.strftime('%d.%m.%Y')} ({day_name})\n"
        f"🔢 **Урок:** {l_num}-й\n"
        f"📖 **Предмет:** {subj.name if subj else ''}\n\n"
        "📢 **Разослать оповещение классу об изменении расписания?**",
        reply_markup=get_date_schedule_notify_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сохранено!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_dt_reset")
async def cb_edit_dt_sched_reset(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    target_d_str = data.get("edit_target_date")
    if not target_d_str:
        await callback.answer("Выберите дату заново", show_alert=True)
        return
    target_d = date.fromisoformat(target_d_str)
    day_name = DAYS_RU.get(target_d.isoweekday(), "")

    await clear_date_schedule(db_session, target_d)
    await auto_shift_active_homeworks(db_session)

    perm_lessons = await get_schedule_for_date(db_session, target_d)
    schedule_lines = [f"{l.lesson_number}. {l.subject.name}" for l in perm_lessons]

    await state.update_data(
        alert_title=f"📅 **{day_name} ({target_d.strftime('%d.%m.%Y')}):**\n_(Расписание возвращено к стандартному)_",
        alert_lines=schedule_lines
    )
    await state.set_state(EditDateScheduleStates.confirm_notification)

    await callback.message.edit_text(
        f"🗑 **Расписание на {target_d.strftime('%d.%m.%Y')} сброшено к постоянному!**\n\n"
        "📢 **Оповестить класс о возврате к стандартному расписанию?**",
        reply_markup=get_date_schedule_notify_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Сброшено!")
    except Exception:
        pass


@router.callback_query(F.data.in_(["adm_dt_notify_groups", "adm_dt_notify_pm", "adm_dt_notify_all", "adm_dt_notify_yes"]))
async def cb_edit_dt_notify_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    title = data.get("alert_title", "Изменение расписания")
    lines = data.get("alert_lines", [])

    to_groups = callback.data in ("adm_dt_notify_groups", "adm_dt_notify_all", "adm_dt_notify_yes")
    to_users = callback.data in ("adm_dt_notify_pm", "adm_dt_notify_all", "adm_dt_notify_yes")

    await send_schedule_change_alert(bot, title, lines, to_groups=to_groups, to_users=to_users)
    await state.clear()
    dest_text = "в чат и в ЛС" if (to_groups and to_users) else ("в чат" if to_groups else "в ЛС")
    await callback.message.edit_text(
        f"📢 **Оповещение об изменении расписания успешно разослано ({dest_text})!**",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer("Разослано!")
    except Exception:
        pass


@router.callback_query(F.data == "adm_dt_notify_no")
async def cb_edit_dt_notify_no(callback: CallbackQuery, state: FSMContext):
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


# ==================== STEP-BY-STEP SCHEDULE WIZARD ====================

@router.callback_query(F.data == "adm_sc_wizard")
async def cb_start_schedule_wizard_permanent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    day_num = data.get("edit_day", 1)
    day_names = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}
    day_name = day_names.get(day_num, "день")

    await state.update_data(wizard_mode="permanent", wizard_lessons={})
    await state.set_state(ScheduleWizardStates.choosing_lesson_count)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{i}", callback_data=f"wiz_cnt_{i}") for i in range(1, 5)],
            [InlineKeyboardButton(text=f"{i}", callback_data=f"wiz_cnt_{i}") for i in range(5, 9)],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )

    await callback.message.edit_text(
        f"🎛 **Конструктор постоянного расписания на {day_name}**\n\n"
        "🔢 **Сколько всего уроков будет в этот день?**\n"
        "Нажмите кнопку с нужным количеством уроков (от 1 до 8):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_dt_wizard")
async def cb_start_schedule_wizard_date(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_d = date.fromisoformat(data["edit_target_date"])
    day_name = DAYS_RU.get(target_d.isoweekday(), "")

    await state.update_data(wizard_mode="date", wizard_lessons={})
    await state.set_state(ScheduleWizardStates.choosing_lesson_count)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{i}", callback_data=f"wiz_cnt_{i}") for i in range(1, 5)],
            [InlineKeyboardButton(text=f"{i}", callback_data=f"wiz_cnt_{i}") for i in range(5, 9)],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )

    await callback.message.edit_text(
        f"🎛 **Конструктор расписания на {day_name} ({target_d.strftime('%d.%m.%Y')})**\n\n"
        "🔢 **Сколько всего уроков будет в этот день?**\n"
        "Нажмите кнопку с нужным количеством уроков (от 1 до 8):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


async def render_wizard_lesson_step(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    total = data["wizard_total"]
    cur = data["wizard_cur"]
    lessons = data.get("wizard_lessons", {})

    mode = data.get("wizard_mode")
    if mode == "permanent":
        day_names = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}
        day_str = f"Постоянное — {day_names.get(data.get('edit_day', 1), '')}"
    else:
        target_d = date.fromisoformat(data["edit_target_date"])
        day_str = f"{DAYS_RU.get(target_d.isoweekday(), '')} ({target_d.strftime('%d.%m.%Y')})"

    preview_lines = []
    for i in range(1, cur):
        name = lessons.get(str(i)) or lessons.get(i)
        val = f"**{name}**" if name else "_— (прочерк / окно)_"
        preview_lines.append(f"  {i}. {val}")
    preview_lines.append(f"👉 **{cur}. [Выбирается сейчас...]**")

    subjects = await get_all_subjects(db_session)
    buttons = []
    row = []
    for s in subjects:
        row.append(InlineKeyboardButton(text=s.name, callback_data=f"wiz_sub_s_{s.id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    ctrl_row = [
        InlineKeyboardButton(text="➖ Прочерк / Окно", callback_data="wiz_sub_skip")
    ]
    if cur > 1:
        ctrl_row.append(InlineKeyboardButton(text="💾 Завершить сейчас", callback_data="wiz_sub_finish"))
    buttons.append(ctrl_row)
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])

    text = (
        f"🎛 **Конструктор расписания ({day_str})**\n"
        f"📌 **Шаг {cur} из {total}:** выбор предмета для **{cur}-го урока**\n\n"
        + "\n".join(preview_lines) + "\n\n"
        "Нажмите на кнопку предмета или «➖ Прочерк / Окно»:"
    )

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")


@router.callback_query(F.data.startswith("wiz_cnt_"))
async def cb_wizard_count_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    cnt = int(callback.data.replace("wiz_cnt_", ""))
    await state.update_data(wizard_total=cnt, wizard_cur=1, wizard_lessons={})
    await state.set_state(ScheduleWizardStates.choosing_subject_for_lesson)
    await render_wizard_lesson_step(callback, state, db_session)
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("wiz_sub_s_"))
async def cb_wizard_subject_chosen(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    subj_id = int(callback.data.replace("wiz_sub_s_", ""))
    subj = await get_subject_by_id(db_session, subj_id)
    subj_name = subj.name if subj else "Предмет"

    data = await state.get_data()
    cur = data.get("wizard_cur", 1)
    total = data.get("wizard_total", 8)
    lessons = data.get("wizard_lessons", {})
    lessons[str(cur)] = subj_name

    cur += 1
    await state.update_data(wizard_cur=cur, wizard_lessons=lessons)

    if cur <= total:
        await render_wizard_lesson_step(callback, state, db_session)
    else:
        await finalize_schedule_wizard(callback, state, db_session)
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "wiz_sub_skip")
async def cb_wizard_subject_skip(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    cur = data.get("wizard_cur", 1)
    total = data.get("wizard_total", 8)
    lessons = data.get("wizard_lessons", {})
    lessons[str(cur)] = None

    cur += 1
    await state.update_data(wizard_cur=cur, wizard_lessons=lessons)

    if cur <= total:
        await render_wizard_lesson_step(callback, state, db_session)
    else:
        await finalize_schedule_wizard(callback, state, db_session)
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "wiz_sub_finish")
async def cb_wizard_subject_finish_early(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    await finalize_schedule_wizard(callback, state, db_session)
    try:
        await callback.answer()
    except Exception:
        pass


async def finalize_schedule_wizard(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    lessons = data.get("wizard_lessons", {})
    mode = data.get("wizard_mode")

    final_lessons = []
    lines = []
    total = data.get("wizard_total", max([int(k) for k in lessons.keys()] or [0]))
    for i in range(1, total + 1):
        name = lessons.get(str(i)) or lessons.get(i)
        if name:
            final_lessons.append((i, name))
            lines.append(f"  {i}. **{name}**")
        else:
            lines.append(f"  {i}. _— (окно / нет урока)_")

    if mode == "permanent":
        day_num = data["edit_day"]
        day_names = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}
        day_name = day_names.get(day_num, "день")

        saved = await save_bulk_permanent_schedule(db_session, day_num, final_lessons)
        await auto_shift_active_homeworks(db_session)
        await state.clear()
        await callback.message.edit_text(
            f"✅ **Постоянное расписание на {day_name} сохранено ({len(saved)} уроков)!**\n\n"
            + "\n".join(lines),
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="Markdown"
        )
    else:
        target_d = date.fromisoformat(data["edit_target_date"])
        day_name = DAYS_RU.get(target_d.isoweekday(), "")
        saved = await save_bulk_date_schedule(db_session, target_d, final_lessons)
        await auto_shift_active_homeworks(db_session)

        await state.update_data(
            alert_title=f"📅 **{day_name} ({target_d.strftime('%d.%m.%Y')}):**",
            alert_lines=lines
        )
        await state.set_state(EditDateScheduleStates.confirm_notification)
        preview = (
            f"✅ **Расписание на {day_name} ({target_d.strftime('%d.%m.%Y')}) сохранено ({len(saved)} ур.)!**\n\n"
            + "\n".join(lines) + "\n\n"
            "📢 **Разослать оповещение классу об изменении расписания?**"
        )
        await callback.message.edit_text(preview, reply_markup=get_date_schedule_notify_keyboard(), parse_mode="Markdown")


# ==================== SUBSTITUTIONS & CANCELLATIONS ====================

@router.callback_query(F.data == "admin_add_sub")
async def cb_start_add_sub(callback: CallbackQuery, state: FSMContext, current_user: User):
    if not is_admin(current_user, callback.from_user.id):
        return

    today = date.today()
    kb = get_inline_calendar("adm_sub", year=today.year, month=today.month, back_callback="admin_cancel")

    await state.set_state(AddSubstitutionStates.entering_date)
    await callback.message.edit_text(
        "🔄 **Замена урока (Шаг 1/4):**\n"
        "Выберите дату на интерактивном календаре:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_nav_adm_sub_"))
async def cb_cal_nav_adm_sub(callback: CallbackQuery):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    kb = get_inline_calendar("adm_sub", year=year, month=month, back_callback="admin_cancel")
    await callback.message.edit_text(
        "🔄 **Замена урока (Шаг 1/4):**\n"
        "Выберите дату на интерактивном календаре:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("cal_act_adm_sub_"))
async def cb_cal_act_adm_sub(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    year = int(parts[4])
    month = int(parts[5])
    day = int(parts[6])
    sub_date = date(year, month, day)

    await state.update_data(sub_date=sub_date.isoformat())

    lesson_btns = [
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_sub_l_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(text=f"{i} урок", callback_data=f"adm_sub_l_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ]

    await state.set_state(AddSubstitutionStates.entering_lesson_num)
    await callback.message.edit_text(
        f"🔢 **Замена на {sub_date.strftime('%d.%m.%Y')} (Шаг 2/4):**\nКакой по счету урок заменяется/отменяется?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=lesson_btns),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_sub_l_"))
async def cb_sub_lesson_chosen(callback: CallbackQuery, state: FSMContext):
    l_num = int(callback.data.replace("adm_sub_l_", ""))
    await state.update_data(lesson_number=l_num)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Замена на другой предмет", callback_data="adm_sub_act_replace")],
            [InlineKeyboardButton(text="❌ Отмена урока (урока не будет)", callback_data="adm_sub_act_cancel")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )

    await state.set_state(AddSubstitutionStates.choosing_action)
    await callback.message.edit_text(
        f"⚡ **{l_num}-й урок (Шаг 3/4):** Что происходит с уроком?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_sub_act_cancel")
async def cb_sub_cancel_lesson(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    sub_date = date.fromisoformat(data["sub_date"])

    sub = await create_substitution(
        session=db_session,
        target_date=sub_date,
        lesson_number=data["lesson_number"],
        old_subject_id=None,
        new_subject_id=None,
        comment="Урок отменен",
        is_cancelled=True
    )
    await auto_shift_active_homeworks(db_session)
    await state.update_data(sub_id=sub.id)

    await state.set_state(AddSubstitutionStates.confirm_notification)

    await callback.message.edit_text(
        f"❌ **Зафиксирована отмена {data['lesson_number']}-го урока на {sub_date.strftime('%d.%m.%Y')}!**\n\n"
        "Отправить мгновенное уведомление всему классу?",
        reply_markup=get_notify_confirm_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data == "adm_sub_act_replace")
async def cb_sub_action_replace(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    subjects = await get_all_subjects(db_session)
    buttons = [[InlineKeyboardButton(text=s.name, callback_data=f"adm_sub_new_s_{s.id}")] for s in subjects]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])

    await state.set_state(AddSubstitutionStates.choosing_new_subject)
    await callback.message.edit_text(
        "📖 **Какой предмет будет вместо прежнего?**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_sub_new_s_"))
async def cb_sub_new_subject_chosen(callback: CallbackQuery, state: FSMContext):
    new_s_id = int(callback.data.replace("adm_sub_new_s_", ""))
    await state.update_data(new_subject_id=new_s_id)
    await state.set_state(AddSubstitutionStates.entering_comment)

    await callback.message.edit_text(
        "📝 **Напишите комментарий (например, имя учителя или тему) либо отправьте `-`:**",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(AddSubstitutionStates.entering_comment)
async def msg_sub_finish(message: Message, state: FSMContext, db_session: AsyncSession):
    text = message.text.strip()
    comment = text if text != "-" else None

    data = await state.get_data()
    sub_date = date.fromisoformat(data["sub_date"])

    sub = await create_substitution(
        session=db_session,
        target_date=sub_date,
        lesson_number=data["lesson_number"],
        old_subject_id=None,
        new_subject_id=data.get("new_subject_id"),
        comment=comment,
        is_cancelled=False
    )
    await auto_shift_active_homeworks(db_session)
    await state.update_data(sub_id=sub.id)

    await state.set_state(AddSubstitutionStates.confirm_notification)

    await message.answer(
        f"✅ **Замена сохранена!**\n"
        f"📅 **Дата:** {sub_date.strftime('%d.%m.%Y')}\n"
        f"🔢 **Урок:** {data['lesson_number']}\n\n"
        "Отправить срочное оповещение всему классу?",
        reply_markup=get_notify_confirm_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.in_(["sub_notify_groups", "sub_notify_pm", "sub_notify_all", "sub_notify_yes"]))
async def cb_sub_broadcast(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession, bot: Bot):
    data = await state.get_data()
    sub_date_str = data.get("sub_date") or data.get("edit_target_date")
    if not sub_date_str:
        await callback.answer("Данные для оповещения не найдены", show_alert=True)
        await state.clear()
        return

    to_groups = callback.data in ("sub_notify_groups", "sub_notify_all", "sub_notify_yes")
    to_users = callback.data in ("sub_notify_pm", "sub_notify_all", "sub_notify_yes")

    sub_date = date.fromisoformat(sub_date_str)
    l_num = data.get("lesson_number")

    if l_num is not None:
        notif_text = (
            f"🚨 **ВНИМАНИЕ! ЗАМЕНА В РАСПИСАНИИ 11 «Б»!** 🚨\n\n"
            f"📅 **Дата:** {sub_date.strftime('%d.%m.%Y')}\n"
            f"🔢 **{l_num}-й урок** изменен!\n\n"
            "Пожалуйста, проверьте расписание в боте или в Mini App."
        )

        sent_count = 0

        if to_users:
            students = await get_notifiable_users(db_session)
            for s in students:
                try:
                    await bot.send_message(chat_id=s.tg_id, text=notif_text, parse_mode="Markdown")
                    sent_count += 1
                except Exception:
                    pass

        if to_groups:
            groups = await get_approved_group_chats(db_session)
            for g in groups:
                try:
                    await bot.send_message(
                        chat_id=g.chat_id,
                        message_thread_id=g.topic_schedule_id,
                        text=notif_text,
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                except Exception:
                    pass

        await state.clear()
        dest_text = "в чат и в ЛС" if (to_groups and to_users) else ("в чат" if to_groups else "в ЛС")
        await callback.message.edit_text(
            f"📢 Оповещение о замене успешно разослано ({dest_text}) {sent_count} получателям!",
            reply_markup=get_admin_panel_keyboard()
        )
        try:
            await callback.answer("Разослано!")
        except Exception:
            pass
    else:
        # Full date schedule broadcast fallback
        day_name = DAYS_RU.get(sub_date.isoweekday(), "")
        title = data.get("alert_title", f"📅 **{day_name} ({sub_date.strftime('%d.%m.%Y')}):**")
        lines = data.get("alert_lines", [])
        try:
            await send_schedule_change_alert(bot, title, lines, to_groups=to_groups, to_users=to_users)
        except Exception as e:
            logger.error(f"Error sending schedule change alert: {e}")
        await state.clear()
        dest_text = "в чат и в ЛС" if (to_groups and to_users) else ("в чат" if to_groups else "в ЛС")
        await callback.message.edit_text(
            f"📢 **Оповещение об изменении расписания успешно разослано ({dest_text})!**",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="Markdown"
        )
        try:
            await callback.answer("Разослано!")
        except Exception:
            pass


@router.callback_query(F.data == "sub_notify_no")
async def cb_sub_no_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_sub = "sub_date" in data and "lesson_number" in data
    await state.clear()
    msg = "✅ Замена сохранена без массового оповещения." if is_sub else "🔇 Изменения сохранены без рассылки оповещения."
    await callback.message.edit_text(
        msg,
        reply_markup=get_admin_panel_keyboard()
    )
    try:
        await callback.answer()
    except Exception:
        pass
