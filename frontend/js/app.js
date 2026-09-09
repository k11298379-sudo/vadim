// Application state for 11 "Б"
let currentDate = new Date();
let selectedDateStr = formatDateISO(currentDate);
let activeTab = "schedule";
let isCalendarPicked = false;

// Calendar modal state
let calViewDate = new Date();


function formatDateISO(d) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

const MONTHS_RU = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
];

const DAYS_SHORT = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

// Academic Calendar helpers in JS
const VACATIONS = [
  { start: "2026-10-26", end: "2026-11-03", name: "Осенние каникулы" },
  { start: "2026-12-31", end: "2027-01-10", name: "Зимние каникулы" },
  { start: "2027-03-27", end: "2027-04-04", name: "Весенние каникулы" },
  { start: "2027-05-27", end: "2027-08-31", name: "Летние каникулы" }
];

const WORKING_SATURDAYS = new Set(["2027-02-20"]);

function getDayType(isoStr, dayOfWeek) {
  for (const v of VACATIONS) {
    if (isoStr >= v.start && isoStr <= v.end) {
      return "vacation";
    }
  }
  if (WORKING_SATURDAYS.has(isoStr)) {
    return "working_sat";
  }
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    return "weekend";
  }
  return "regular";
}

// Initialize
async function initApp() {
  initTabs();
  initCalendarModal();
  initPhotoViewer();
  renderDateSelector();
  await loadUserData();
  loadDutyWidget();
  loadDailyFactWidget();

  const urlParams = new URLSearchParams(window.location.search);
  const roomId = urlParams.get("room");
  const gameType = urlParams.get("game");
  const tabParam = urlParams.get("tab");
  if (roomId) {
    switchTab("games");
    if (window.GAMES && typeof window.GAMES.openOnlineRoom === "function") {
      window.GAMES.openOnlineRoom(roomId, gameType);
    }
  } else if (tabParam) {
    switchTab(tabParam);
  } else {
    loadTabContent(activeTab);
  }
}

function switchTab(tab) {
  const btn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
  if (btn) {
    btn.click();
  } else {
    if (activeTab === "games" && tab !== "games") {
      if (window.GAMES && typeof window.GAMES.cleanup === "function") {
        window.GAMES.cleanup();
      }
    }
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach((p) => p.classList.add("hidden"));
    const targetPane = document.getElementById(`pane-${tab}`);
    if (targetPane) targetPane.classList.remove("hidden");

    const dateWrapper = document.getElementById("date-selector-wrapper");
    const dutyWidget = document.getElementById("duty-widget");
    const factWidget = document.getElementById("daily-fact-widget");
    if (tab === "bells" || tab === "ege" || tab === "games") {
      if (dateWrapper) dateWrapper.classList.add("hidden");
      if (dutyWidget) dutyWidget.classList.add("hidden");
    } else {
      if (dateWrapper) dateWrapper.classList.remove("hidden");
      if (dutyWidget) dutyWidget.classList.remove("hidden");
    }

    if (factWidget) {
      if (tab === "schedule") {
        const content = document.getElementById("fact-content");
        if (content && content.textContent && content.textContent.trim()) {
          factWidget.classList.remove("hidden");
        }
      } else {
        factWidget.classList.add("hidden");
      }
    }

    activeTab = tab;
    loadTabContent(tab);
  }
}
window.switchTab = switchTab;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  initApp();
}

async function loadUserData() {
  const userBadge = document.getElementById("user-badge");
  if (!userBadge) return;

  try {
    const me = await api.getMe();
    window.currentUser = me;
    if (window.GAMES && typeof window.GAMES.updateTesterStatus === "function") {
      window.GAMES.updateTesterStatus(Boolean(me && me.is_tester));
    }
    if (me && me.full_name) {
      const roleTag = me.role === "admin" ? " • 👑 Админ" : "";
      userBadge.textContent = me.full_name + roleTag;
    } else {
      userBadge.textContent = "Ученик 11 «Б»";
    }
  } catch (e) {
    console.warn("Could not load user data:", e.message);
    userBadge.textContent = "Ученик 11 «Б»";
  }
}





async function loadDutyWidget() {
  const badge = document.getElementById("duty-badge");
  const members = document.getElementById("duty-members");
  if (!badge || !members) return;

  try {
    const data = await api.getDuty();
    badge.textContent = data.name || `Группа ${data.current_group}`;
    members.textContent = data.members || "Состав уточняется";
  } catch (e) {
    console.warn("Could not load duty data:", e.message);
    const widget = document.getElementById("duty-widget");
    if (widget) widget.classList.add("hidden");
  }
}

async function loadDailyFactWidget() {
  const badge = document.getElementById("fact-category");
  const title = document.getElementById("fact-title");
  const content = document.getElementById("fact-content");
  const widget = document.getElementById("daily-fact-widget");
  if (!badge || !title || !content || !widget) return;

  try {
    const data = await api.getDailyFact();
    if (data && data.fact) {
      badge.textContent = data.category || "Факт";
      title.textContent = data.title || "Знаете ли вы?";
      content.textContent = data.fact;
      if (activeTab === "schedule") {
        widget.classList.remove("hidden");
      } else {
        widget.classList.add("hidden");
      }
    } else {
      widget.classList.add("hidden");
    }
  } catch (e) {
    console.warn("Could not load daily fact:", e.message);
    widget.classList.add("hidden");
  }
}



// Tab navigation
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      if (tab === activeTab) return;

      if (activeTab === "games" && tab !== "games") {
        if (window.GAMES && typeof window.GAMES.cleanup === "function") {
          window.GAMES.cleanup();
        }
      }

      haptic.selection();
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.add("hidden"));
      const targetPane = document.getElementById(`pane-${tab}`);
      if (targetPane) targetPane.classList.remove("hidden");

      // Hide date selector and duty widget on bells, ege, and games tabs
      const dateWrapper = document.getElementById("date-selector-wrapper");
      const dutyWidget = document.getElementById("duty-widget");
      if (tab === "bells" || tab === "ege" || tab === "games") {
        if (dateWrapper) dateWrapper.classList.add("hidden");
        if (dutyWidget) dutyWidget.classList.add("hidden");
      } else {
        if (dateWrapper) dateWrapper.classList.remove("hidden");
        if (dutyWidget) dutyWidget.classList.remove("hidden");
      }

      // Interesting fact widget is strictly visible ONLY on the "schedule" (Уроки) tab
      const factWidget = document.getElementById("daily-fact-widget");
      if (factWidget) {
        if (tab === "schedule") {
          const content = document.getElementById("fact-content");
          if (content && content.textContent && content.textContent.trim()) {
            factWidget.classList.remove("hidden");
          }
        } else {
          factWidget.classList.add("hidden");
        }
      }

      activeTab = tab;
      loadTabContent(tab);
    });
  });
}

// --- INTERACTIVE CALENDAR MODAL ---
function initCalendarModal() {
  const openBtn = document.getElementById("open-calendar-btn");
  const closeBtn = document.getElementById("cal-close-btn");
  const modal = document.getElementById("calendar-modal");
  const prevBtn = document.getElementById("cal-prev-month");
  const nextBtn = document.getElementById("cal-next-month");
  const todayBtn = document.getElementById("cal-today-btn");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      haptic.impact("light");
      const [y, m, d] = selectedDateStr.split("-").map(Number);
      calViewDate = new Date(y, m - 1, 1);
      renderCalendarGrid();
      modal.classList.remove("hidden");
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      haptic.selection();
      modal.classList.add("hidden");
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      haptic.selection();
      calViewDate.setMonth(calViewDate.getMonth() - 1);
      renderCalendarGrid();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      haptic.selection();
      calViewDate.setMonth(calViewDate.getMonth() + 1);
      renderCalendarGrid();
    });
  }

  if (todayBtn) {
    todayBtn.addEventListener("click", () => {
      haptic.impact("medium");
      const today = new Date();
      selectedDateStr = formatDateISO(today);
      isCalendarPicked = false;
      modal.classList.add("hidden");
      renderDateSelector();
      loadTabContent(activeTab);
    });
  }
}

function renderCalendarGrid() {
  const monthTitle = document.getElementById("cal-month-title");
  const daysGrid = document.getElementById("cal-days-grid");
  if (!monthTitle || !daysGrid) return;

  const year = calViewDate.getFullYear();
  const month = calViewDate.getMonth();
  monthTitle.textContent = `${MONTHS_RU[month]} ${year}`;

  daysGrid.innerHTML = "";

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  let firstDayIndex = firstDayOfMonth.getDay(); // 0 is Sun
  firstDayIndex = (firstDayIndex === 0 ? 6 : firstDayIndex - 1); // convert to Mon=0

  const totalDays = lastDayOfMonth.getDate();

  // Blank days before first day
  for (let i = 0; i < firstDayIndex; i++) {
    const blank = document.createElement("div");
    blank.className = "py-2";
    daysGrid.appendChild(blank);
  }

  const todayIso = formatDateISO(new Date());

  for (let day = 1; day <= totalDays; day++) {
    const dObj = new Date(year, month, day);
    const iso = formatDateISO(dObj);
    const dayOfWeek = dObj.getDay();
    const dayType = getDayType(iso, dayOfWeek);
    const isSelected = (iso === selectedDateStr);
    const isToday = (iso === todayIso);

    const btn = document.createElement("button");
    btn.className = `py-1.5 px-1 rounded-xl text-xs font-semibold flex flex-col items-center justify-center transition-all ${
      isSelected
        ? "bg-blue-600 text-white shadow-md shadow-blue-500/30 scale-105 font-bold"
        : isToday
        ? "border-2 border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-slate-800"
        : dayType === "vacation"
        ? "bg-amber-100/70 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 hover:bg-amber-200"
        : "text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
    }`;

    let badge = "";
    if (dayType === "vacation") badge = `<span class="text-[9px] block">🌴</span>`;
    else if (dayType === "working_sat") badge = `<span class="text-[9px] block">💼</span>`;

    btn.innerHTML = `
      <span>${day}</span>
      ${badge}
    `;

    btn.addEventListener("click", () => {
      haptic.impact("light");
      selectedDateStr = iso;
      isCalendarPicked = true;
      document.getElementById("calendar-modal").classList.add("hidden");
      renderDateSelector();
      loadTabContent(activeTab);
    });

    daysGrid.appendChild(btn);
  }
}

// Date selector horizontal strip
function renderDateSelector() {
  const container = document.getElementById("date-selector");
  if (!container) return;

  container.innerHTML = "";
  const [y, m, d] = selectedDateStr.split("-").map(Number);
  const baseDate = new Date(y, m - 1, d);

  const dayOfWeek = baseDate.getDay();
  const diff = baseDate.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Monday
  const startOfWeek = new Date(baseDate);
  startOfWeek.setDate(diff);

  for (let i = 0; i < 6; i++) {
    const d = new Date(startOfWeek);
    d.setDate(startOfWeek.getDate() + i);
    const iso = formatDateISO(d);
    const isSelected = (iso === selectedDateStr);
    const dayType = getDayType(iso, d.getDay());

    const btn = document.createElement("button");
    btn.className = `flex flex-col items-center justify-center py-2 px-3 rounded-2xl text-xs transition-all ${
      isSelected
        ? "bg-blue-600 text-white font-bold shadow-md shadow-blue-500/20 scale-105"
        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
    }`;

    let icon = "";
    if (dayType === "vacation") icon = " 🌴";

    btn.innerHTML = `
      <span class="text-[10px] uppercase opacity-75">${DAYS_SHORT[d.getDay()]}${icon}</span>
      <span class="text-sm font-semibold">${d.getDate()}</span>
    `;

    btn.addEventListener("click", () => {
      haptic.impact("light");
      selectedDateStr = iso;
      isCalendarPicked = false;
      renderDateSelector();
      if (activeTab === "schedule") loadSchedule();
      if (activeTab === "homework") loadHomework();
    });

    container.appendChild(btn);
  }
}

async function loadTabContent(tab) {
  if (tab === "schedule") await loadSchedule();
  else if (tab === "homework") await loadHomework();
  else if (tab === "bells") await loadBells();
  else if (tab === "ege") {
    if (window.EGE && typeof window.EGE.init === "function") {
      window.EGE.init();
    }
  } else if (tab === "games") {
    if (window.GAMES && typeof window.GAMES.init === "function") {
      window.GAMES.init();
    }
  }
}

// --- SCHEDULE ---
async function loadSchedule() {
  const list = document.getElementById("schedule-list");
  if (!list) return;

  list.innerHTML = `<div class="text-center py-8 text-slate-400 text-sm animate-pulse">Загрузка расписания 11 «Б»...</div>`;

  try {
    const data = await api.getSchedule(selectedDateStr);
    
    if (data.day_status === "vacation") {
      list.innerHTML = `
        <div class="text-center py-12 theme-card rounded-2xl p-6 border-2 border-amber-500/30 bg-amber-50/50 dark:bg-amber-950/20">
          <span class="text-5xl">🌴</span>
          <h3 class="mt-3 text-base font-bold text-amber-600 dark:text-amber-400">🎉 ${data.status_text}!</h3>
          <p class="mt-1 text-xs text-slate-500">Каникулы — уроков нет, отдыхаем!</p>
        </div>
      `;
      return;
    }

    if (!data.lessons || data.lessons.length === 0) {
      const isWeekend = data.day_status === "weekend";
      list.innerHTML = `
        <div class="text-center py-12 theme-card rounded-2xl p-6">
          <span class="text-5xl">${isWeekend ? "🏖" : "📅"}</span>
          <h3 class="mt-3 text-sm font-bold text-slate-700 dark:text-slate-200">${isWeekend ? data.status_text : "Уроков нет"}</h3>
          <p class="mt-1 text-xs text-slate-500">${isWeekend ? "Выходной день — уроков нет!" : "Расписание на этот день еще не заполнено."}</p>
        </div>
      `;
      return;
    }

    list.innerHTML = "";
    data.lessons.forEach((l) => {
      const card = document.createElement("div");
      card.className = "theme-card rounded-2xl p-4 flex items-center justify-between shadow-sm transition-all";

      let statusBadge = "";


      const commentText = l.comment ? `<p class="text-xs text-amber-600 mt-1 italic">${l.comment}</p>` : "";
      const subjectStyle = l.is_cancelled ? "line-through opacity-50" : "font-semibold";

      card.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-xl bg-blue-50 dark:bg-slate-800 text-blue-600 font-bold flex items-center justify-center text-sm shrink-0">
            ${l.lesson_number}
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="${subjectStyle} text-sm subject-title text-slate-700 dark:text-slate-100">${l.subject_name}</h3>
              ${statusBadge}
            </div>
            <p class="text-xs text-slate-400 mt-0.5">${l.start_time} - ${l.end_time}</p>
            ${commentText}
          </div>
        </div>
      `;

      list.appendChild(card);
    });
  } catch (err) {
    list.innerHTML = `<div class="text-center py-6 text-red-500 text-sm">Ошибка: ${err.message}</div>`;
  }
}

// --- HOMEWORK (ЧЕК-ЛИСТ ДЗ) ---
async function loadHomework() {
  const list = document.getElementById("homework-list");
  if (!list) return;

  const todayStr = formatDateISO(new Date());
  const isPast = selectedDateStr < todayStr;

  list.innerHTML = `<div class="text-center py-8 text-slate-400 text-sm animate-pulse">Загрузка заданий...</div>`;

  try {
    const items = await api.getHomework(selectedDateStr);
    if (!items || items.length === 0) {
      list.innerHTML = `
        <div class="text-center py-12 theme-card rounded-2xl p-6">
          <span class="text-4xl">🎉</span>
          <p class="mt-3 text-sm font-medium text-slate-400">На этот день заданий нет! Можно отдыхать.</p>
        </div>
      `;
      return;
    }

    list.innerHTML = "";

    items.forEach((hw) => {
      const card = document.createElement("div");
      const borderClass = isPast
        ? "border-l-slate-400 dark:border-l-slate-600 opacity-80"
        : (hw.is_completed ? "border-l-emerald-500 opacity-60" : "border-l-blue-500");

      card.className = `theme-card rounded-2xl p-4 shadow-sm transition-all border-l-4 ${borderClass}`;

      const titleStr = hw.title ? `<span class="text-xs text-slate-400"> • ${hw.title}</span>` : "";

      let attHtml = "";
      const photos = (hw.attachments || []).filter(a => a.type === "photo" && a.url);
      const docs = (hw.attachments || []).filter(a => a.type === "document");

      if (photos.length > 0 || docs.length > 0) {
        let photoThumbsHtml = "";
        if (photos.length > 0) {
          const thumbs = photos.map((p, pIdx) => `
            <div class="pv-thumb relative w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden shadow-sm border border-slate-200/80 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 cursor-pointer shrink-0 hover:scale-105 active:scale-95 transition-all group" data-idx="${pIdx}">
              <img src="${p.url}" alt="Фото задания" loading="lazy" class="w-full h-full object-cover" />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/15 transition-colors flex items-end justify-end p-1">
                <span class="text-[9px] bg-black/60 text-white font-bold px-1 rounded shadow">🔍</span>
              </div>
            </div>
          `).join("");

          photoThumbsHtml = `
            <div class="mt-2.5 flex items-center gap-2 overflow-x-auto pb-1 max-w-full">
              ${thumbs}
            </div>
          `;
        }

        let docsHtml = "";
        if (docs.length > 0) {
          const docLinks = docs.map(d => `
            <a href="${d.url || '#'}" download="${d.file_name || 'файл'}" target="_blank" class="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1.5 rounded-xl bg-blue-50 dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-slate-700 hover:bg-blue-100 transition-colors">
              <span>📄</span>
              <span class="truncate max-w-[130px]">${d.file_name || 'Документ'}</span>
              <span>⬇️</span>
            </a>
          `).join("");

          docsHtml = `
            <div class="mt-2 flex items-center gap-1.5 flex-wrap">
              ${docLinks}
            </div>
          `;
        }

        attHtml = photoThumbsHtml + docsHtml;
      }

      const toggleBtnHtml = isPast ? "" : `
        <button class="toggle-btn w-7 h-7 rounded-xl border-2 flex items-center justify-center transition-all shrink-0 mt-0.5 ${
          hw.is_completed ? "bg-emerald-500 border-emerald-500 text-white shadow-sm shadow-emerald-500/30" : "border-slate-300 dark:border-slate-600 hover:border-blue-500"
        }" data-id="${hw.id}" title="Отметить выполненным">
          ${hw.is_completed ? "✓" : ""}
        </button>
      `;

      const titleCompletedClass = (!isPast && hw.is_completed) ? "line-through opacity-60" : "";

      card.innerHTML = `
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h3 class="font-bold text-sm subject-title text-slate-700 dark:text-slate-100 ${titleCompletedClass}">${hw.subject_name}</h3>
              ${titleStr}
            </div>
            <p class="text-sm mt-2 leading-relaxed homework-desc text-slate-600 dark:text-slate-200 whitespace-pre-line">${hw.description}</p>
            ${attHtml}
          </div>
          ${toggleBtnHtml}
        </div>
      `;

      // При клике на превью открываем полноэкранный просмотр фото
      if (photos.length > 0) {
        const thumbEls = card.querySelectorAll(".pv-thumb");
        thumbEls.forEach(th => {
          th.addEventListener("click", () => {
            const idx = parseInt(th.getAttribute("data-idx"), 10) || 0;
            openPhotoGallery(photos, idx, hw.subject_name, hw.description);
          });
        });
      }

      // Interactive Toggle handler (только для актуальных ДЗ)
      const toggleBtn = card.querySelector(".toggle-btn");
      if (toggleBtn) {
        toggleBtn.addEventListener("click", async () => {
          haptic.impact("medium");
          try {
            const res = await api.toggleHomework(hw.id);
            hw.is_completed = res.is_completed;
            loadHomework();
          } catch (e) {
            alert("Не удалось изменить статус");
          }
        });
      }

      list.appendChild(card);
    });
  } catch (err) {
    list.innerHTML = `<div class="text-center py-6 text-red-500 text-sm">Ошибка: ${err.message}</div>`;
  }
}

// --- BELLS (ЗВОНКИ) ---
async function loadBells() {
  const list = document.getElementById("bells-list");
  if (!list) return;

  list.innerHTML = `<div class="text-center py-8 text-slate-400 text-sm animate-pulse">Загрузка расписания звонков...</div>`;


  try {
    const bells = await api.getBells();
    list.innerHTML = "";
    bells.forEach((b) => {
      const card = document.createElement("div");
      card.className = "theme-card rounded-2xl p-4 flex items-center justify-between shadow-sm border border-slate-200/40 dark:border-slate-800/80 hover:scale-[1.01] transition-all";
      
      let breakBadge = "";
      if (b.break_duration && b.break_duration > 0) {
        const isLong = b.break_duration >= 15;
        breakBadge = `
          <span class="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full ${
            isLong 
              ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800" 
              : "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
          }">
            ${b.break_duration} мин. перемена
          </span>
        `;
      } else {
        breakBadge = `<span class="text-[10px] font-medium text-slate-400">Конец уроков 🎉</span>`;
      }

      card.innerHTML = `
        <div class="flex items-center gap-3.5">
          <div class="w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white font-black flex items-center justify-center text-sm shadow-md shadow-blue-500/20">
            ${b.lesson_number}
          </div>
          <div>
            <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">${b.lesson_number} урок</span>
            <span class="text-sm font-semibold font-mono text-slate-500 dark:text-slate-400">${b.start_time} – ${b.end_time}</span>
          </div>

        </div>
        <div class="text-right">
          ${breakBadge}
        </div>
      `;
      list.appendChild(card);
    });
  } catch (err) {
    list.innerHTML = `<div class="text-center py-6 text-red-500 text-sm">Ошибка: ${err.message}</div>`;
  }
}

// ==================== PHOTO VIEWER / LIGHTBOX MODAL ====================
let galleryPhotos = [];
let galleryCurrentIndex = 0;
let pvScale = 1.0;
let pvTranslateX = 0;
let pvTranslateY = 0;
let pvIsDragging = false;
let pvStartX = 0;
let pvStartY = 0;
let pvInitialPinchDist = 0;
let pvInitialScale = 1.0;

function initPhotoViewer() {
  const modal = document.getElementById("photo-viewer-modal");
  const closeBtn = document.getElementById("pv-close-btn");
  const prevBtn = document.getElementById("pv-prev-btn");
  const nextBtn = document.getElementById("pv-next-btn");
  const zoomInBtn = document.getElementById("pv-zoom-in");
  const zoomOutBtn = document.getElementById("pv-zoom-out");
  const viewport = document.getElementById("pv-viewport");

  if (!modal) return;

  closeBtn?.addEventListener("click", closePhotoGallery);

  prevBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    if (galleryCurrentIndex > 0) {
      showGalleryImage(galleryCurrentIndex - 1);
    }
  });

  nextBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    if (galleryCurrentIndex < galleryPhotos.length - 1) {
      showGalleryImage(galleryCurrentIndex + 1);
    }
  });

  zoomInBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    pvScale = Math.min(4.0, pvScale + 0.5);
    updateImageTransform();
  });

  zoomOutBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    pvScale = Math.max(1.0, pvScale - 0.5);
    if (pvScale === 1.0) {
      pvTranslateX = 0;
      pvTranslateY = 0;
    }
    updateImageTransform();
  });

  // Double tap / double click to toggle zoom
  let lastTap = 0;
  viewport?.addEventListener("click", (e) => {
    if (e.target.closest("button") || e.target.closest("a")) return;
    const now = Date.now();
    if (now - lastTap < 300) {
      if (pvScale > 1.0) {
        pvScale = 1.0;
        pvTranslateX = 0;
        pvTranslateY = 0;
      } else {
        pvScale = 2.5;
      }
      updateImageTransform();
    }
    lastTap = now;
  });

  // Mouse Drag / Pan
  viewport?.addEventListener("mousedown", (e) => {
    if (pvScale > 1.0) {
      pvIsDragging = true;
      pvStartX = e.clientX - pvTranslateX;
      pvStartY = e.clientY - pvTranslateY;
    }
  });

  window.addEventListener("mousemove", (e) => {
    if (pvIsDragging && pvScale > 1.0) {
      pvTranslateX = e.clientX - pvStartX;
      pvTranslateY = e.clientY - pvStartY;
      updateImageTransform();
    }
  });

  window.addEventListener("mouseup", () => {
    pvIsDragging = false;
  });

  // Touch Pinch-to-Zoom & Pan
  viewport?.addEventListener("touchstart", (e) => {
    if (e.touches.length === 2) {
      pvInitialPinchDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      pvInitialScale = pvScale;
    } else if (e.touches.length === 1 && pvScale > 1.0) {
      pvIsDragging = true;
      pvStartX = e.touches[0].clientX - pvTranslateX;
      pvStartY = e.touches[0].clientY - pvTranslateY;
    }
  }, { passive: false });

  viewport?.addEventListener("touchmove", (e) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const currentDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      if (pvInitialPinchDist > 0) {
        pvScale = Math.min(4.0, Math.max(1.0, pvInitialScale * (currentDist / pvInitialPinchDist)));
        updateImageTransform();
      }
    } else if (e.touches.length === 1 && pvIsDragging && pvScale > 1.0) {
      e.preventDefault();
      pvTranslateX = e.touches[0].clientX - pvStartX;
      pvTranslateY = e.touches[0].clientY - pvStartY;
      updateImageTransform();
    }
  }, { passive: false });

  viewport?.addEventListener("touchend", (e) => {
    if (e.touches.length < 2) {
      pvInitialPinchDist = 0;
    }
    if (e.touches.length === 0) {
      pvIsDragging = false;
      if (pvScale <= 1.0) {
        pvScale = 1.0;
        pvTranslateX = 0;
        pvTranslateY = 0;
        updateImageTransform();
      }
    }
  });

  // Keyboard navigation
  window.addEventListener("keydown", (e) => {
    if (modal.classList.contains("hidden")) return;
    if (e.key === "Escape") closePhotoGallery();
    if (e.key === "ArrowLeft" && galleryCurrentIndex > 0) showGalleryImage(galleryCurrentIndex - 1);
    if (e.key === "ArrowRight" && galleryCurrentIndex < galleryPhotos.length - 1) showGalleryImage(galleryCurrentIndex + 1);
  });
}

function updateImageTransform() {
  const img = document.getElementById("pv-image");
  if (img) {
    img.style.transform = `translate(${pvTranslateX}px, ${pvTranslateY}px) scale(${pvScale})`;
  }
}

function openPhotoGallery(photos, startIndex, title = "", desc = "") {
  galleryPhotos = photos;
  galleryCurrentIndex = startIndex || 0;

  const modal = document.getElementById("photo-viewer-modal");
  const titleEl = document.getElementById("pv-caption-title");
  const descEl = document.getElementById("pv-caption-desc");

  if (!modal) return;

  if (titleEl) titleEl.textContent = title;
  if (descEl) descEl.textContent = desc;

  modal.classList.remove("hidden");
  setTimeout(() => {
    modal.classList.remove("opacity-0");
  }, 10);

  showGalleryImage(galleryCurrentIndex);
}

function showGalleryImage(idx) {
  galleryCurrentIndex = idx;
  pvScale = 1.0;
  pvTranslateX = 0;
  pvTranslateY = 0;
  updateImageTransform();

  const photo = galleryPhotos[idx];
  const img = document.getElementById("pv-image");
  const counter = document.getElementById("pv-counter");
  const dlBtn = document.getElementById("pv-download-btn");
  const prevBtn = document.getElementById("pv-prev-btn");
  const nextBtn = document.getElementById("pv-next-btn");
  const titleEl = document.getElementById("pv-caption-title");
  const descEl = document.getElementById("pv-caption-desc");

  // Support both raw string URL or object with .url
  const url = typeof photo === "string" ? photo : (photo?.url || "");

  if (img && url) {
    img.src = url;
    if (photo && typeof photo === "object" && photo.title) {
      img.alt = photo.title;
    } else if (titleEl?.textContent) {
      img.alt = titleEl.textContent;
    }
  }

  // Update caption if individual photo object provides it
  if (photo && typeof photo === "object") {
    if (photo.title && titleEl) titleEl.textContent = photo.title;
    if (photo.desc && descEl) descEl.textContent = photo.desc;
  }

  if (counter) {
    counter.textContent = `${idx + 1} / ${galleryPhotos.length}`;
  }

  if (dlBtn && url) {
    dlBtn.href = url;
    const filename = url.split("/").pop() || `photo_${idx + 1}.webp`;
    dlBtn.setAttribute("download", filename);
  }

  if (prevBtn) {
    if (galleryPhotos.length > 1 && idx > 0) {
      prevBtn.classList.remove("hidden");
    } else {
      prevBtn.classList.add("hidden");
    }
  }

  if (nextBtn) {
    if (galleryPhotos.length > 1 && idx < galleryPhotos.length - 1) {
      nextBtn.classList.remove("hidden");
    } else {
      nextBtn.classList.add("hidden");
    }
  }
}

function closePhotoGallery() {
  const modal = document.getElementById("photo-viewer-modal");
  if (!modal) return;
  modal.classList.add("opacity-0");
  setTimeout(() => {
    modal.classList.add("hidden");
    pvScale = 1.0;
    pvTranslateX = 0;
    pvTranslateY = 0;
    updateImageTransform();
  }, 200);
}

// Ensure globally accessible
window.openPhotoGallery = openPhotoGallery;
window.closePhotoGallery = closePhotoGallery;


