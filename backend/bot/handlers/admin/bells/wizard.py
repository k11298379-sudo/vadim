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
from backend.bot.keyboards.admin_kb import (
    get_admin_panel_keyboard, get_cancel_keyboard, get_date_bells_notify_keyboard
)
from backend.bot.keyboards.calendar import get_inline_calendar
from backend.bot.services.notifier import send_schedule_change_alert
from backend.bot.handlers.schedule import DAYS_RU
from backend.bot.handlers.admin.helpers import is_admin, parse_bells_text
from backend.bot.handlers.admin.states import EditBellStates, EditDateBellStates, EditBreakStates, BellWizardStates

router = Router(name='admin_bells_wiz_router')

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

        await callback.message.edit_text(
            f"✅ **Расписание звонков на {day_name} ({target_d.strftime('%d.%m.%Y')}) сохранено!**\n\n"
            "📢 **Разослать классу и в беседы уведомление об изменении звонков?**",
            reply_markup=get_date_bells_notify_keyboard(),
            parse_mode="Markdown"
        )
    try:
        await callback.answer("Звонки сохранены!")
    except Exception:
        pass
