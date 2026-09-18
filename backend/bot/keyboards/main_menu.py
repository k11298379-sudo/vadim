from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from backend.config import settings

def get_main_keyboard(is_admin: bool = False, user_id: int | None = None) -> ReplyKeyboardMarkup:
    kb = []
    
    # Buttons to open Telegram Mini App with explicit user ID attachment (Telegram requires HTTPS for WebAppInfo)
    url = settings.WEBAPP_URL
    app_buttons = []
    if url and url.startswith("https://"):
        if user_id:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}tg_user_id={user_id}"

        webapp_btn = KeyboardButton(
            text="📱 Mini App 11 «Б»",
            web_app=WebAppInfo(url=url)
        )
        app_buttons.append(webapp_btn)

    nat_url = f"{settings.BASE_URL.rstrip('/')}/app/natbirzha"
    if nat_url.startswith("https://"):
        if user_id:
            separator = "&" if "?" in nat_url else "?"
            nat_url = f"{nat_url}{separator}tg_user_id={user_id}"
        nat_btn = KeyboardButton(
            text="📈 НАТБИРЖА",
            web_app=WebAppInfo(url=nat_url)
        )
        app_buttons.append(nat_btn)
    else:
        app_buttons.append(KeyboardButton(text="📈 НАТБИРЖА"))

    if app_buttons:
        kb.append(app_buttons)

    kb.extend([
        [
            KeyboardButton(text="📅 Расписание"),
            KeyboardButton(text="📚 Домашка")
        ],
        [
            KeyboardButton(text="🔔 Звонки"),
            KeyboardButton(text="🧹 График дежурств")
        ],
        [
            KeyboardButton(text="🎂 Дни рождения"),
            KeyboardButton(text="💡 Интересный факт")
        ],
        [
            KeyboardButton(text="⏳ Сейчас"),
            KeyboardButton(text="☀️ До лета осталось")
        ]
    ])

    bottom_row = []
    if is_admin:
        bottom_row.append(KeyboardButton(text="👑 Панель управления"))
    bottom_row.append(KeyboardButton(text="⚙️ Настройки"))
    kb.append(bottom_row)

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="11 «Б» Класс • Выберите раздел..."
    )
