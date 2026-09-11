# Журнал изменений разработки (CHANGELOG_DEV.md)

> Данный файл предназначен исключительно для отслеживания изменений между тестовой веткой (`dev`) и основным ботом (`master`/`main`).
> **Внимание:** Этот файл локальный, в Telegram не рассылается.

---

## 📌 Краткий обзор изменений

1. **Удаление лишних кнопок в панели управления**
   - Убраны «Список предметов», «Изменить имя» и «Удалить пользователя» из главного меню админ-панели (функционал управления пользователями полностью перенесён в «Права доступа»).
   - Кнопка «🔔 Звонки и перемены» сделана полноразмерной на всю строку.

2. **Функция «Сделать текущее расписание постоянным»**
   - В меню расписания конкретной даты добавлена кнопка «📌 Сделать это расписание постоянным». При нажатии уроки выбранной даты становятся базовым шаблоном для соответствующего дня недели, а оверрайд очищается.
   - В меню постоянного расписания добавлена кнопка «📅 Скопировать с конкретной даты» с интерактивным выбором даты из календаря.

3. **Отмена вечерних уведомлений по пятницам**
   - Вечерний дайджест в 19:00 больше не рассылается по пятницам (на субботу нет домашнего задания).
   - В ручной команде тестирования `/test_digest` добавлен параметр `force=True`, позволяющий админу запускать тестовую рассылку в любой день.

4. **Заявки на вход и авторизацию чатов всем администраторам**
   - Уведомления о новых заявках пользователей и групповых чатов теперь отправляются всем пользователям с ролью `admin` и владельцу `ADMIN_ID`.
   - Добавлена защита от повторной обработки: если один админ одобрил/отклонил заявку, повторное нажатие кнопки другим админом выдает корректное уведомление «Заявка уже обработана».

5. **Настройки пользователя и уведомления о столовой**
   - Добавлено меню «⚙️ Настройки» с тумблерами:
     - Напоминание о столовой (после 5 урока приходят 3 сообщения в ЛС).
     - Внутриигровая валюта и игры.
   - Сервис столовой `backend/bot/services/canteen.py` отслеживает завершение 5 урока с учётом динамического расписания звонков на текущую дату.

6. **Внутриигровая экосистема валюты и игра «Дурак» со ставками**
   - Команды `/cash` (баланс) и `/work` (школьный заработок раз в 4 часа).
   - В игре «Дурак» реализованы ставки комнат (от 0 до 10 000 монет). Победитель забирает банк всех участников.

7. **Логирование и управление памятью**
   - Кольцевой буфер `MemoryLogHandler` в ОЗУ для предотвращения утечек памяти при длительной работе бота. Команды админа для инспекции логов.

8. **Архитектурная декомпозиция крупных файлов**
   - Крупные модули разделены на небольшие пакеты (`backend/bot/handlers/admin/schedule/`, `homework/`, `bells/`, `duty/`, `backend/db/crud/`, `backend/api/routers/`, `frontend/src/js/ege/`).
   - 100% обратная совместимость через `__init__.py`.

---

## 🗂 Список измененных и добавленных файлов

### База данных (Модели и CRUD):
- `backend/db/models.py`:
  - Добавлены поля в `User`:
    - `canteen_reminder_enabled: bool` (default `True`)
    - `currency_ecosystem_enabled: bool` (default `True`)
    - `coins: int` (default `100`)
    - `last_work_at: Optional[datetime]` (default `None`)
- `backend/db/crud/users.py`:
  - Добавлена `get_admin_users(session: AsyncSession) -> List[User]`.
  - Добавлены функции для настроек и валюты: `toggle_user_canteen_reminder`, `toggle_user_currency_ecosystem`, `perform_user_work`, `add_user_coins`, `get_currency_leaderboard`.
- `backend/db/crud/__init__.py`:
  - Экспорт `get_admin_users` и новых функций.

### Сервисы и планировщик:
- `backend/bot/services/scheduler.py`:
  - `evening_digest_job`: изменен триггер на `CronTrigger(day_of_week="mon-thu,sat,sun", ...)` для исключения пятницы.
- `backend/bot/services/notifier.py`:
  - `send_evening_digest(bot, target_date=None, force=False)`: добавлена проверка пропуска пятницы (`today_weekday == 5` или `day_of_week in (6, 7)` при `not force`).
  - Добавлена функция `notify_all_admins(bot, session, text, reply_markup=None)`.
- `backend/bot/services/canteen.py`:
  - Сервис отправки напоминаний о столовой после 5 урока.
- `backend/main.py`:
  - `check_and_send_evening_digest_on_startup`: добавлен пропуск пятницы и субботы (`today.isoweekday() in (5, 6)`).

### Обработчики бота:
- `backend/bot/keyboards/admin_kb.py`:
  - В `get_admin_panel_keyboard()` удалены кнопки «Список предметов», «Изменить имя», «Удалить пользователя». Расширена кнопка звонков.
- `backend/bot/handlers/admin/schedule/permanent.py`:
  - Добавлена кнопка «📅 Скопировать с конкретной даты».
  - Добавлены обработчики `cb_start_copy_from_date`, `cb_cal_nav_adm_sccpy`, `cb_cal_act_adm_sccpy`.
- `backend/bot/handlers/admin/schedule/date_override.py`:
  - Добавлена кнопка «📌 Сделать это расписание постоянным».
  - Добавлен обработчик `cb_edit_dt_sched_make_permanent`.
- `backend/bot/handlers/start.py`:
  - Регистрационные заявки отправляются через `notify_all_admins`.
  - Добавлена проверка `target_user.role != "pending"` в `callback_admin_approve` и `callback_admin_reject`.
- `backend/bot/middlewares/auth.py`:
  - Оповещение о новых пользователях отправляется через `notify_all_admins`.
- `backend/bot/handlers/group.py`:
  - Оповещение о заявках чатов отправляется через `notify_all_admins`.
  - Добавлена проверка `existing_chat.role != "pending"` в `cb_admin_approve_chat` и `cb_admin_reject_chat`.
- `backend/bot/handlers/admin/menu.py`:
  - В `cmd_test_digest` добавлен флаг `force=True`.
- `backend/bot/handlers/settings.py` & `backend/bot/keyboards/settings_kb.py`:
  - Меню настроек и переключатели.
- `backend/bot/handlers/economy.py`:
  - Команды `/cash` и `/work`.

### Правила и стандарты кода:
- `AGENTS.md` & `GEMINI.md`:
  - Инструкции для AI-ассистента: ограничение размера файлов (до 350-400 строк), запрет на создание файлов-монолитов, правила декомпозиции в пакеты с обратной совместимостью и обязательный протокол верификации тестами.

---

## 🚀 Пошаговая инструкция для переноса на основного бота

Когда вы будете готовы применить эти изменения на основном сервере:

1. **Обновление структуры БД (SQLite / PostgreSQL)**:
   Если база данных уже создана и работает, добавьте 4 новых столбца в таблицу `users` (если они ещё не добавлены):
   ```sql
   ALTER TABLE users ADD COLUMN canteen_reminder_enabled BOOLEAN DEFAULT 1;
   ALTER TABLE users ADD COLUMN currency_ecosystem_enabled BOOLEAN DEFAULT 1;
   ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 100;
   ALTER TABLE users ADD COLUMN last_work_at TIMESTAMP;
   ```
   *(При создании чистой базы таблицы создаются автоматически через SQLAlchemy).*

2. **Слияние кода**:
   - Перенесите измененные файлы или сделайте `git merge dev` (или перенесите ветку).
   - Запустите тесты:
     ```bash
     python tests/test_suite.py
     ```

3. **Перезапуск службы бота**:
   - Перезапустите бота `systemctl restart botdz` (или соответствующий процесс).
