// ==============================================================================
// МОДУЛЬ ТРЕНАЖЕРА ЕГЭ ДЛЯ MINI APP (Задание 4: Ударения, Задание 5: Паронимы)
// ==============================================================================

(function () {
  const RUSSIAN_VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ";
  const EGE_DATA = window.EGE_DATA || {};

  let currentSubject = "russian";
  let currentTask = 4; // 4 (Ударения) или 5 (Паронимы)
  let currentSubTab = "quiz"; // 'quiz' or 'dict'

  // ==================== STATE ДЛЯ ЗАДАНИЯ 4 (УДАРЕНИЯ) ====================
  let currentPosFilter = "all";
  let dictSearchQuery = "";
  let quizWords = [];
  let quizIndex = 0;
  let quizAnswered = false;
  let quizCorrectCount = 0;
  let quizMistakes = [];
  let quizTotal = 10;

  // ==================== STATE ДЛЯ ЗАДАНИЯ 5 (ПАРОНИМЫ) ====================
  let paronymSearchQuery = "";
  let paronymLetterFilter = "Все";
  let pQuizQuestions = [];
  let pQuizIndex = 0;
  let pQuizAnswered = false;
  let pQuizCorrectCount = 0;
  let pQuizMistakes = [];
  let pQuizTotal = 10;
  let lastPSelectedWord = null;
  let lastPAnswerCorrect = false;

  function shuffleArray(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function initEge() {
    const container = document.getElementById("pane-ege");
    if (!container) return;
    renderEge();
  }

  function renderEge() {
    const container = document.getElementById("pane-ege");
    if (!container) return;

    container.innerHTML = `
      <!-- Subject Header & Selector -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-base font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-1.5">
              <span>🎓</span> Тренажер ЕГЭ
            </h2>
            <p class="text-xs text-slate-400 font-medium">Подготовка по официальным банкам ФИПИ</p>
          </div>
          <span class="text-[11px] font-bold px-2 py-0.5 rounded-lg bg-indigo-50 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-slate-700">ФИПИ 2026</span>
        </div>

        <!-- Subjects Carousel/Pills -->
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
          ${(EGE_DATA.subjects || []).map(s => `
            <button onclick="window.EGE.selectSubject('${s.id}')" class="px-3 py-1.5 rounded-xl font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              currentSubject === s.id
                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700'
            }">
              <span>${s.icon}</span>
              <span>${s.name}</span>
            </button>
          `).join('')}
        </div>
      </div>

      <!-- Content Area for Selected Subject -->
      <div id="ege-subject-content" class="space-y-4">
        ${renderSubjectContent()}
      </div>
    `;
  }

  function renderSubjectContent() {
    const subj = (EGE_DATA.subjects || []).find(s => s.id === currentSubject);
    const availableTasks = (subj?.tasks || []).filter(t => t.available !== false);

    if (!subj || availableTasks.length === 0) {
      return `
        <div class="theme-card rounded-2xl p-8 text-center bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 space-y-2">
          <span class="text-3xl">${subj?.icon || '📚'}</span>
          <h3 class="font-bold text-slate-800 dark:text-slate-100 text-sm">Заданий пока нет</h3>
          <p class="text-xs text-slate-400 max-w-xs mx-auto">Для предмета «${subj?.name || ''}» пока нет добавленных заданий.</p>
        </div>
      `;
    }

    // Task Selection Cards
    return `
      <!-- Tasks list -->
      <div class="theme-card rounded-2xl p-3 bg-white dark:bg-slate-800 border border-slate-200/70 dark:border-slate-700 space-y-2">
        <div class="flex items-center justify-between px-1">
          <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Задания ЕГЭ</span>
          <span class="text-[11px] text-blue-600 dark:text-blue-400 font-bold">${availableTasks.length} доступно</span>
        </div>
        <div class="grid grid-cols-1 gap-1.5">
          ${availableTasks.map(t => {
            const isActive = currentTask === t.number;
            const cardStyle = isActive
              ? "border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 ring-1 ring-blue-500 shadow-sm"
              : "border-slate-200/80 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-300 cursor-pointer";

            return `
              <div onclick="window.EGE.selectTask(${t.number})"
                   class="p-2.5 rounded-xl border transition-all ${cardStyle}">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="w-6 h-6 rounded-lg ${isActive ? 'bg-blue-600 text-white shadow-sm' : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200'} font-black text-xs flex items-center justify-center">${t.number}</span>
                    <div>
                      <h4 class="text-xs font-bold text-slate-800 dark:text-slate-100">${t.title}</h4>
                      <p class="text-[11px] text-slate-400">${t.desc}</p>
                    </div>
                  </div>
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400'}">${isActive ? 'Выбрано' : 'Открыть'}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <!-- Active Task Container -->
      <div class="space-y-3">
        ${currentSubject === "math" && currentTask === 18
          ? renderMathTask18()
          : `
            <!-- Sub-tabs: Quiz vs Dictionary -->
            <div class="flex items-center p-1 rounded-2xl bg-slate-200/70 dark:bg-slate-800/90 text-xs font-bold">
              <button id="ege-subtab-btn-quiz" onclick="window.EGE.setSubTab('quiz')" class="flex-1 py-2 rounded-xl transition-all flex items-center justify-center gap-1.5 ${
                currentSubTab === 'quiz'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'
              }">
                <span>🎯</span>
                <span>Тренажёр</span>
              </button>
              <button id="ege-subtab-btn-dict" onclick="window.EGE.setSubTab('dict')" class="flex-1 py-2 rounded-xl transition-all flex items-center justify-center gap-1.5 ${
                currentSubTab === 'dict'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'
              }">
                <span>📖</span>
                <span>${currentTask === 5 ? 'Словарь паронимов' : 'Словарь ФИПИ'}</span>
              </button>
            </div>

            <!-- Tab Body -->
            <div id="ege-subtab-container">
              ${currentTask === 5 
                ? (currentSubTab === 'quiz' ? renderParonymsQuizTab() : renderParonymsDictTab())
                : (currentSubTab === 'quiz' ? renderQuizTab() : renderDictTab())
              }
            </div>
          `
        }
      </div>
    `;
  }

  function selectSubject(subjectId) {
    currentSubject = subjectId;
    if (subjectId === "math") {
      currentTask = 18;
      math18ShowSolution = false;
    } else if (subjectId === "russian") {
      if (currentTask !== 4 && currentTask !== 5) currentTask = 4;
    }
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    renderEge();
  }

  function selectTask(taskNumber) {
    if (currentTask === taskNumber) return;
    currentTask = taskNumber;
    currentSubTab = "quiz";
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    renderEge();
  }

  function updateSubTabNavDOM() {
    const btnQuiz = document.getElementById("ege-subtab-btn-quiz");
    const btnDict = document.getElementById("ege-subtab-btn-dict");
    if (!btnQuiz || !btnDict) return;

    const activeClasses = ["bg-white", "dark:bg-slate-700", "text-blue-600", "dark:text-blue-400", "shadow-sm"];
    const inactiveClasses = ["text-slate-500", "dark:text-slate-400", "hover:text-slate-700"];

    if (currentSubTab === "quiz") {
      btnQuiz.classList.add(...activeClasses);
      btnQuiz.classList.remove(...inactiveClasses);
      btnDict.classList.remove(...activeClasses);
      btnDict.classList.add(...inactiveClasses);
    } else {
      btnDict.classList.add(...activeClasses);
      btnDict.classList.remove(...inactiveClasses);
      btnQuiz.classList.remove(...activeClasses);
      btnQuiz.classList.add(...inactiveClasses);
    }
  }

  function setSubTab(tab) {
    currentSubTab = tab;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    const subContainer = document.getElementById("ege-subtab-container");
    if (!subContainer) {
      renderEge();
      return;
    }
    updateSubTabNavDOM();
    if (currentTask === 5) {
      subContainer.innerHTML = currentSubTab === "quiz" ? renderParonymsQuizTab() : renderParonymsDictTab();
    } else {
      subContainer.innerHTML = currentSubTab === "quiz" ? renderQuizTab() : renderDictTab();
    }
  }

  // ==============================================================================
  // РАЗДЕЛ МАТЕМАТИКИ: ЗАДАНИЕ 18 (ПАРАМЕТРЫ) • 153 ЗАДАЧИ
  // ==============================================================================
  let math18CurrentIdx = 0;
  let math18TopicFilter = "Все";
  let math18SearchQuery = "";
  let math18ShowSolution = false;

  const MATH18_TOPICS = [
    "Все",
    "📊 С графиками",
    "Графический метод",
    "Окружности и прямые",
    "Уголки и модули",
    "Замена переменной",
    "Инвариантность и чётность",
    "Монотонность и оценка",
    "Тригонометрия",
    "Квадратный трёхчлен и Виет"
  ];

  function getFilteredMath18Tasks() {
    const all = window.EGE_MATH18_TASKS || [];
    return all.filter(t => {
      let topicMatch = true;
      if (math18TopicFilter === "📊 С графиками") {
        topicMatch = t.has_graphics === true;
      } else if (math18TopicFilter !== "Все") {
        topicMatch = (t.topic === math18TopicFilter);
      }

      let searchMatch = true;
      if (math18SearchQuery) {
        const q = math18SearchQuery.toLowerCase().trim();
        searchMatch = String(t.num) === q || 
                      t.id.toLowerCase().includes(q) ||
                      (t.topic && t.topic.toLowerCase().includes(q));
      }

      return topicMatch && searchMatch;
    });
  }

  function renderMathTask18() {
    const all = window.EGE_MATH18_TASKS || [];
    const filtered = getFilteredMath18Tasks();
    if (filtered.length > 0 && math18CurrentIdx >= filtered.length) {
      math18CurrentIdx = 0;
    }

    const t = filtered[math18CurrentIdx];

    return `
      <div class="space-y-3">
        <!-- Search & Filter Bar -->
        <div class="theme-card rounded-2xl p-3 bg-white dark:bg-slate-800 border border-slate-200/70 dark:border-slate-700 space-y-2.5">
          <div class="flex items-center gap-2">
            <div class="relative flex-1">
              <input type="text" value="${math18SearchQuery}" 
                     placeholder="Поиск по номеру (напр. 88) или #ID..." 
                     oninput="window.EGE.onMath18Search(this.value)"
                     class="w-full pl-8 pr-3 py-2 text-xs font-semibold rounded-xl bg-slate-50 dark:bg-slate-700/60 border border-slate-200 dark:border-slate-600 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <span class="absolute left-2.5 top-2.5 text-xs text-slate-400">🔍</span>
            </div>
            <button onclick="window.EGE.randomMath18Task()" class="px-3 py-2 rounded-xl bg-blue-50 dark:bg-slate-700 hover:bg-blue-100 text-xs font-bold text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-slate-600 transition-colors flex items-center gap-1 whitespace-nowrap" title="Случайная задача">
              <span>🎲</span>
            </button>
          </div>

          <!-- Filter Pills -->
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
            ${MATH18_TOPICS.map(topic => {
              const isActive = math18TopicFilter === topic;
              return `
                <button onclick="window.EGE.selectMath18Topic('${topic}')" class="px-2.5 py-1 rounded-xl font-bold whitespace-nowrap transition-all text-[11px] ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-slate-50 dark:bg-slate-700/70 text-slate-600 dark:text-slate-300 border border-slate-200/80 dark:border-slate-600 hover:border-blue-300'
                }">
                  ${topic}
                </button>
              `;
            }).join('')}
          </div>

          <!-- Carousel / Numbers -->
          <div class="pt-0.5">
            <div class="flex items-center justify-between text-[10px] font-bold text-slate-400 mb-1 px-0.5">
              <span>Каталог заданий</span>
              <span class="text-blue-600 dark:text-blue-400 font-bold">${filtered.length} из ${all.length}</span>
            </div>
            <div class="flex items-center gap-1 overflow-x-auto pb-1 no-scrollbar text-xs" id="math18-carousel">
              ${filtered.map((item, idx) => {
                const isActive = idx === math18CurrentIdx;
                return `
                  <button onclick="window.EGE.selectMath18Task(${idx})"
                          class="px-2.5 py-1 rounded-xl font-black text-xs whitespace-nowrap transition-all flex items-center gap-0.5 ${
                            isActive 
                              ? 'bg-blue-600 text-white shadow-sm scale-105' 
                              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                          }">
                    <span>№${item.num}</span>
                    ${item.has_graphics ? '<span class="text-[8px] opacity-75">📊</span>' : ''}
                  </button>
                `;
              }).join('')}
            </div>
          </div>
        </div>

        <!-- Task Content Card -->
        ${!t ? `
          <div class="theme-card rounded-2xl p-6 text-center bg-white dark:bg-slate-800 border border-slate-200/70 dark:border-slate-700 space-y-2">
            <span class="text-3xl">🔍</span>
            <h3 class="font-bold text-sm">Задачи не найдены</h3>
            <p class="text-xs text-slate-400">Попробуйте изменить поисковый запрос или фильтр.</p>
          </div>
        ` : `
          <div class="theme-card rounded-2xl p-3.5 sm:p-4 bg-white dark:bg-slate-800 border border-slate-200/70 dark:border-slate-700 space-y-3.5">
            
            <!-- Top bar -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-7 h-7 rounded-xl bg-blue-600 text-white font-black text-xs flex items-center justify-center shadow-sm">
                  ${t.num}
                </span>
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs font-black text-slate-900 dark:text-white">Задача №${t.num}</span>
                    <span class="text-[11px] font-bold text-blue-600 dark:text-blue-400">#${t.id}</span>
                  </div>
                  <p class="text-[10px] text-slate-400">Параметры • ЕГЭ Профиль</p>
                </div>
              </div>

              <div class="flex items-center gap-1">
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                  ${t.topic}
                </span>
                ${t.has_graphics ? `
                  <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60 flex items-center gap-0.5">
                    <span>📊</span> График
                  </span>
                ` : ''}
              </div>
            </div>

            <!-- Condition -->
            <div class="p-2.5 sm:p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-700/60 space-y-1.5">
              <div class="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <span>Условие задачи:</span>
                <button onclick="window.EGE.viewPhoto(['${t.cond_img}'], 0, 'Задача №${t.num}', 'Условие')" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline">Увеличить 🔍</button>
              </div>
              <div class="bg-white rounded-lg p-1.5 sm:p-2 cursor-zoom-in border border-slate-200/60 shadow-xs" onclick="window.EGE.viewPhoto(['${t.cond_img}'], 0, 'Задача №${t.num}', 'Условие')">
                <img src="${t.cond_img}" alt="Условие №${t.num}" class="w-full h-auto rounded-md mx-auto" loading="lazy" />
              </div>
            </div>

            <!-- Solution Button -->
            <button onclick="window.EGE.toggleMath18Solution()" class="w-full py-2.5 px-3 rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5 ${
              math18ShowSolution 
                ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm shadow-blue-500/25' 
                : 'bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200'
            }">
              <span>${math18ShowSolution ? '📖 Скрыть решение' : '📝 Открыть полное пошаговое решение'}</span>
            </button>

            <!-- Solution Stream (Chronological order of text, formulas & diagrams) -->
            ${math18ShowSolution ? `
              <div class="space-y-2.5 pt-1 border-t border-slate-100 dark:border-slate-700/60">
                <div class="flex items-center justify-between px-1">
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs">📝</span>
                    <h4 class="text-[11px] font-black uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Ход решения ${t.has_graphics ? '(с графиками)' : ''}:
                    </h4>
                  </div>
                  <span class="text-[10px] font-bold text-slate-400">${t.sol_imgs.length} стр.</span>
                </div>

                <div class="space-y-2.5">
                  ${t.sol_imgs.map((s_img, s_idx) => `
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-2 border border-slate-200 dark:border-slate-700/80 shadow-xs space-y-1">
                      <div class="flex items-center justify-between px-1 text-[9px] font-bold text-slate-400">
                        <span>Часть ${s_idx + 1} из ${t.sol_imgs.length}</span>
                        <button onclick="window.EGE.viewPhoto(${JSON.stringify(t.sol_imgs).replace(/"/g, '&quot;')}, ${s_idx}, 'Задача №${t.num}', 'Решение (часть ${s_idx+1})')" class="text-blue-600 dark:text-blue-400 hover:underline">
                          Увеличить 🔍
                        </button>
                      </div>
                      <div class="cursor-zoom-in overflow-hidden rounded-lg bg-white p-0.5" onclick="window.EGE.viewPhoto(${JSON.stringify(t.sol_imgs).replace(/"/g, '&quot;')}, ${s_idx}, 'Задача №${t.num}', 'Решение (часть ${s_idx+1})')">
                        <img src="${s_img}" alt="Решение №${t.num} (${s_idx+1})" class="w-full h-auto rounded-md mx-auto" loading="lazy" />
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            <!-- Pagination -->
            <div class="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/60 text-xs">
              <button onclick="window.EGE.prevMath18Task()" ${math18CurrentIdx === 0 ? 'disabled class="opacity-40 cursor-not-allowed"' : ''} 
                      class="px-3 py-1.5 rounded-xl font-bold bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors flex items-center gap-1">
                <span>←</span> <span>Назад</span>
              </button>
              <span class="text-slate-400 font-bold text-[11px]">${math18CurrentIdx + 1} из ${filtered.length}</span>
              <button onclick="window.EGE.nextMath18Task()" ${math18CurrentIdx === filtered.length - 1 ? 'disabled class="opacity-40 cursor-not-allowed"' : ''} 
                      class="px-3 py-1.5 rounded-xl font-bold bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors flex items-center gap-1">
                <span>Вперёд</span> <span>→</span>
              </button>
            </div>

          </div>
        `}
      </div>
    `;
  }

  function selectMath18Topic(topic) {
    math18TopicFilter = topic;
    math18CurrentIdx = 0;
    math18ShowSolution = false;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    renderEge();
  }

  function onMath18Search(query) {
    math18SearchQuery = query;
    math18CurrentIdx = 0;
    math18ShowSolution = false;
    renderEge();
  }

  function selectMath18Task(idx) {
    math18CurrentIdx = idx;
    math18ShowSolution = false;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    renderEge();
  }

  function nextMath18Task() {
    const filtered = getFilteredMath18Tasks();
    if (math18CurrentIdx < filtered.length - 1) {
      math18CurrentIdx++;
      math18ShowSolution = false;
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.selectionChanged();
      }
      renderEge();
    }
  }

  function prevMath18Task() {
    if (math18CurrentIdx > 0) {
      math18CurrentIdx--;
      math18ShowSolution = false;
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.selectionChanged();
      }
      renderEge();
    }
  }

  function randomMath18Task() {
    const filtered = getFilteredMath18Tasks();
    if (filtered.length === 0) return;
    math18CurrentIdx = Math.floor(Math.random() * filtered.length);
    math18ShowSolution = false;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
    }
    renderEge();
  }

  function toggleMath18Solution() {
    math18ShowSolution = !math18ShowSolution;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    renderEge();
  }

  function viewPhoto(photos, idx, title, desc) {
    const arr = Array.isArray(photos) ? photos : [photos];
    const total = arr.length;
    const normPhotos = arr.map((p, i) => {
      const itemDesc = (total > 1) ? `Часть ${i + 1} из ${total}` : (desc || "");
      if (typeof p === "string") {
        return { url: p, title: title || "", desc: itemDesc };
      }
      return { ...p, title: p.title || title || "", desc: p.desc || itemDesc };
    });

    if (typeof window.openPhotoGallery === "function") {
      window.openPhotoGallery(normPhotos, idx || 0, title || "", desc || "");
    }
  }

  // ==============================================================================
  // РАЗДЕЛ ЗАДАНИЯ 5: ПАРОНИМЫ (СЛОВАРЬ + ТРЕНАЖЕР)
  // ==============================================================================

  function renderParonymsDictTab() {
    const pData = window.PARONYMS_DATA || { groups: [], letters: [] };
    const query = paronymSearchQuery.toLowerCase().trim();

    const filtered = pData.groups.filter(g => {
      if (paronymLetterFilter !== "Все" && g.letter !== paronymLetterFilter) {
        return false;
      }
      if (query) {
        const inTitle = g.title.toLowerCase().includes(query);
        const inWords = g.words.some(w => 
          w.word.toLowerCase().includes(query) || 
          w.meaning.toLowerCase().includes(query) ||
          w.examples.some(ex => ex.toLowerCase().includes(query))
        );
        return inTitle || inWords;
      }
      return true;
    });

    return `
      <div class="space-y-3">
        <!-- Search bar -->
        <div class="relative">
          <input
            type="text"
            value="${paronymSearchQuery}"
            oninput="window.EGE.onParonymSearch(this.value)"
            placeholder="Поиск паронима, толкования или примера..."
            class="w-full px-3.5 py-2.5 pl-9 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
          />
          <span class="absolute left-3 top-2.5 text-slate-400 text-xs">🔍</span>
          ${paronymSearchQuery ? `
            <button onclick="window.EGE.onParonymSearch('')" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 text-xs font-bold">✕</button>
          ` : ''}
        </div>

        <!-- Alphabet Pills -->
        <div class="flex items-center gap-1 overflow-x-auto pb-1 no-scrollbar text-[11px] font-bold">
          ${(pData.letters || []).map(l => `
            <button onclick="window.EGE.setPLetterFilter('${l}')" class="px-2.5 py-1 rounded-lg whitespace-nowrap transition-all ${
              paronymLetterFilter === l
                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700'
            }">
              ${l}
            </button>
          `).join('')}
        </div>

        <!-- Group Count and Note -->
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>Найдено групп: <b>${filtered.length}</b> из ${pData.groups.length}</span>
          <span class="text-indigo-600 dark:text-indigo-400 font-bold">ФИПИ 2026</span>
        </div>

        <!-- Groups Cards List -->
        <div class="space-y-2.5 max-h-[60vh] overflow-y-auto pr-1">
          ${filtered.length === 0 ? `
            <div class="text-center py-10 theme-card rounded-2xl p-6 text-slate-400 text-xs space-y-2">
              <span class="text-3xl">🔍</span>
              <p>По запросу «${paronymSearchQuery}» ничего не найдено</p>
            </div>
          ` : filtered.map(g => `
            <div class="theme-card rounded-2xl p-3.5 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-3">
              <!-- Group Title Header -->
              <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-2">
                <h3 class="text-xs font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="w-5 h-5 rounded-md bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 text-[10px] font-extrabold flex items-center justify-center">${g.letter}</span>
                  <span>${g.title}</span>
                </h3>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300">
                  ${g.words.length === 2 ? 'пара' : `${g.words.length} слова`}
                </span>
              </div>

              <!-- Words Meanings & Examples -->
              <div class="space-y-2">
                ${g.words.map(w => `
                  <div class="p-2.5 rounded-xl bg-slate-50/80 dark:bg-slate-700/30 border border-slate-100 dark:border-slate-700/40 space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-black text-blue-600 dark:text-blue-400 capitalize tracking-wide">${w.word}</span>
                    </div>
                    <p class="text-[11px] text-slate-700 dark:text-slate-300 leading-relaxed font-medium">${w.meaning}</p>
                    <div class="pt-1 flex items-center flex-wrap gap-1">
                      <span class="text-[10px] font-bold text-slate-400">Примеры:</span>
                      ${w.examples.map(ex => `
                        <span class="text-[10px] px-2 py-0.5 rounded-md bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/60 dark:border-slate-700 font-medium italic">
                          ${ex}
                        </span>
                      `).join('')}
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  function renderParonymsQuizTab() {
    if (pQuizQuestions.length === 0) {
      return renderPQuizSetup();
    }
    if (pQuizIndex >= pQuizQuestions.length) {
      return renderPQuizResults();
    }
    return renderPQuizQuestion();
  }

  function renderPQuizSetup() {
    const pData = window.PARONYMS_DATA || { questions: [] };
    const storedMistakes = getStoredPMistakes();
    const totalAvailable = pData.questions.length;

    return `
      <div class="theme-card rounded-3xl p-5 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-4">
        <div class="text-center space-y-1.5">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white text-2xl flex items-center justify-center mx-auto shadow-md shadow-blue-500/25">
            🎯
          </div>
          <h3 class="text-sm font-black text-slate-900 dark:text-white">Тренажер: Паронимы (Задание 5)</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">
            Отрабатывай лексическое значение и сочетаемость паронимов в реальных предложениях формата КИМ ЕГЭ.
          </p>
        </div>

        <!-- Question count selection -->
        <div class="space-y-2">
          <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Количество вопросов:</span>
          <div class="grid grid-cols-4 gap-1.5">
            ${[10, 25, 50, 'all'].map(cnt => {
              const label = cnt === 'all' ? `Все (${totalAvailable})` : cnt;
              const isSelected = (pQuizTotal === cnt || (cnt === 'all' && pQuizTotal === totalAvailable));
              return `
                <button onclick="window.EGE.setPQuizTotal(${cnt === 'all' ? totalAvailable : cnt})" class="py-2.5 rounded-xl font-bold text-xs transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25 ring-2 ring-blue-400'
                    : 'bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                }">
                  ${label}
                </button>
              `;
            }).join('')}
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-2 pt-2">
          <button onclick="window.EGE.startPQuiz(false)" class="w-full py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] text-white font-extrabold text-sm shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2">
            <span>🚀 Начать тренировку</span>
          </button>

          ${storedMistakes.length > 0 ? `
            <button onclick="window.EGE.startPMistakesQuiz()" class="w-full py-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-amber-700 dark:text-amber-300 font-bold text-xs hover:bg-amber-100 transition-all flex items-center justify-center gap-2">
              <span>⚠️ Повторить ошибки (${storedMistakes.length})</span>
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }

  function renderPQuizQuestion() {
    const current = pQuizQuestions[pQuizIndex];
    if (!current) return renderPQuizResults();

    const progressPercent = Math.round(((pQuizIndex + (pQuizAnswered ? 1 : 0)) / pQuizQuestions.length) * 100);

    // Format sentence: replace _____ with a highlighted placeholder
    const formattedSentence = current.sentence.replace(
      "_____",
      `<span class="inline-block px-3 py-0.5 rounded-lg bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 font-black border border-blue-200 dark:border-blue-700 mx-1 shadow-sm">[ ? ]</span>`
    );

    return `
      <div class="theme-card rounded-3xl p-5 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-4">
        <!-- Progress Header -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-500 dark:text-slate-400">Вопрос ${pQuizIndex + 1} из ${pQuizQuestions.length}</span>
            <div class="flex items-center gap-1.5">
              <span class="text-emerald-600 font-bold">✓ ${pQuizCorrectCount}</span>
              <span class="text-rose-500 font-bold">✗ ${pQuizMistakes.length}</span>
              <button onclick="window.EGE.resetPQuiz()" class="text-slate-400 hover:text-slate-600 ml-1 text-xs">✕ Выйти</button>
            </div>
          </div>
          <div class="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
            <div class="h-full bg-blue-600 rounded-full transition-all duration-300" style="width: ${progressPercent}%"></div>
          </div>
        </div>

        <!-- Question Prompt -->
        <div class="text-center space-y-1">
          <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Вставьте подходящий пароним:</span>
        </div>

        <!-- Sentence Card -->
        <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/70 dark:border-slate-700 text-center">
          <p class="text-sm font-medium text-slate-800 dark:text-slate-100 leading-relaxed">
            «${formattedSentence}»
          </p>
        </div>

        <!-- Paronym Options Buttons -->
        <div class="grid grid-cols-1 gap-2 pt-1">
          ${current.options.map(opt => {
            const isCorrect = opt.toLowerCase() === current.correct.toLowerCase();
            const isSelected = lastPSelectedWord && opt.toLowerCase() === lastPSelectedWord.toLowerCase();

            let btnClass = "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border-slate-200/90 dark:border-slate-700 hover:border-blue-500 hover:bg-blue-50/40 cursor-pointer active:scale-[0.98]";
            if (pQuizAnswered) {
              if (isCorrect) {
                btnClass = "bg-emerald-500 text-white border-emerald-600 font-black shadow-md shadow-emerald-500/25 ring-2 ring-emerald-400";
              } else if (isSelected) {
                btnClass = "bg-rose-500 text-white border-rose-600 font-black ring-2 ring-rose-400 animate-shake";
              } else {
                btnClass = "bg-slate-100 dark:bg-slate-800/60 text-slate-400 opacity-50 border-slate-200 dark:border-slate-700 cursor-default";
              }
            }

            return `
              <button
                ${pQuizAnswered ? 'disabled' : ''}
                onclick="window.EGE.answerPQuestion('${opt}')"
                class="w-full py-3 px-4 rounded-2xl border-2 text-xs font-bold transition-all flex items-center justify-between ${btnClass}">
                <span class="capitalize text-sm font-extrabold">${opt}</span>
                ${pQuizAnswered && isCorrect ? '<span>✓</span>' : ''}
                ${pQuizAnswered && isSelected && !isCorrect ? '<span>✗</span>' : ''}
              </button>
            `;
          }).join('')}
        </div>

        <!-- Feedback & Explanations -->
        ${pQuizAnswered ? `
          <div class="p-3.5 rounded-2xl ${lastPAnswerCorrect ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40 text-emerald-800 dark:text-emerald-300' : 'bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-rose-800 dark:text-rose-300'} text-xs space-y-1.5 transition-all">
            <div class="flex items-center gap-2 font-bold text-sm">
              <span>${lastPAnswerCorrect ? '🎉 Верно!' : '❌ Ошибка!'}</span>
              <span>Правильно: <u class="capitalize font-black">${current.correct}</u></span>
            </div>
            <p class="text-[11px] opacity-90 leading-relaxed font-medium">${current.explanation}</p>
          </div>

          <button onclick="window.EGE.nextPQuestion()" class="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-extrabold text-sm shadow-md shadow-blue-500/25 transition-all flex items-center justify-center gap-2">
            <span>Дальше ➜</span>
          </button>
        ` : `
          <div class="text-center text-[11px] text-slate-400">
            Нажмите на верный вариант, чтобы проверить свой ответ
          </div>
        `}
      </div>
    `;
  }

  function renderPQuizResults() {
    const total = pQuizQuestions.length;
    const percent = Math.round((pQuizCorrectCount / total) * 100);
    const hasMistakes = pQuizMistakes.length > 0;

    // Save mistakes to localStorage
    savePMistakes(pQuizMistakes);

    return `
      <div class="theme-card rounded-3xl p-6 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm text-center space-y-5">
        <div class="w-16 h-16 mx-auto rounded-3xl bg-gradient-to-tr ${percent >= 80 ? 'from-emerald-500 to-teal-500 shadow-emerald-500/25' : percent >= 50 ? 'from-amber-500 to-yellow-500 shadow-amber-500/25' : 'from-rose-500 to-orange-500 shadow-rose-500/25'} text-white text-3xl flex items-center justify-center shadow-lg">
          ${percent >= 80 ? '🏆' : percent >= 50 ? '👍' : '💪'}
        </div>

        <div class="space-y-1">
          <h3 class="text-lg font-black text-slate-900 dark:text-white">Тренировка завершена!</h3>
          <p class="text-xs text-slate-400">Результат: ${pQuizCorrectCount} из ${total} верных (${percent}%)</p>
        </div>

        <!-- Mistakes breakdown if any -->
        ${hasMistakes ? `
          <div class="text-left space-y-2 pt-2 border-t border-slate-100 dark:border-slate-700">
            <span class="text-xs font-bold text-rose-500">Вопросы с ошибками (${pQuizMistakes.length}):</span>
            <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
              ${pQuizMistakes.map(m => `
                <div class="p-2.5 rounded-xl bg-rose-50/70 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 text-xs space-y-1">
                  <p class="text-[11px] text-slate-700 dark:text-slate-300 font-medium">«${m.sentence}»</p>
                  <p class="text-[11px] font-bold text-emerald-600">Верный ответ: ${m.correct}</p>
                </div>
              `).join('')}
            </div>
          </div>
        ` : `
          <div class="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 text-xs font-bold">
            🌟 Отличный результат! Ни одной ошибки в паронимах!
          </div>
        `}

        <div class="space-y-2 pt-2">
          ${hasMistakes ? `
            <button onclick="window.EGE.startPMistakesQuiz()" class="w-full py-3 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 active:scale-[0.98] text-white font-extrabold text-xs shadow-md shadow-amber-500/25 transition-all flex items-center justify-center gap-2">
              <span>🔄 Отработать только ошибки (${pQuizMistakes.length})</span>
            </button>
          ` : ''}

          <button onclick="window.EGE.resetPQuiz()" class="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-extrabold text-xs shadow-md shadow-blue-500/25 transition-all">
            <span>🎯 Начать новую тренировку</span>
          </button>
        </div>
      </div>
    `;
  }

  function setPLetterFilter(letter) {
    paronymLetterFilter = letter;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderParonymsDictTab();
  }

  function onParonymSearch(query) {
    paronymSearchQuery = query;
    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderParonymsDictTab();
  }

  function setPQuizTotal(total) {
    pQuizTotal = total;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderParonymsQuizTab();
  }

  function startPQuiz(isMistakes = false) {
    const pData = window.PARONYMS_DATA || { questions: [] };
    const pool = pData.questions;

    if (!pool || pool.length === 0) return;

    // Shuffle pool using Fisher-Yates
    const shuffled = shuffleArray(pool);

    // Deduplicate by question ID or sentence
    const seen = new Set();
    const uniquePool = [];
    for (const q of shuffled) {
      const key = q.id !== undefined ? String(q.id) : (q.sentence || "").trim().toLowerCase();
      if (key && !seen.has(key)) {
        seen.add(key);
        uniquePool.push(q);
      }
    }

    const count = Math.min(pQuizTotal, uniquePool.length);
    pQuizQuestions = uniquePool.slice(0, count);

    pQuizIndex = 0;
    pQuizAnswered = false;
    pQuizCorrectCount = 0;
    pQuizMistakes = [];
    lastPSelectedWord = null;
    lastPAnswerCorrect = false;

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
    }

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderParonymsQuizTab();
  }

  function startPMistakesQuiz() {
    const mistakes = getStoredPMistakes();
    if (!mistakes || mistakes.length === 0) return;

    // Deduplicate mistakes by id or sentence
    const seen = new Set();
    const uniqueMistakes = [];
    for (const q of mistakes) {
      const key = q && q.id !== undefined ? String(q.id) : (q && q.sentence ? q.sentence.trim().toLowerCase() : "");
      if (key && !seen.has(key)) {
        seen.add(key);
        uniqueMistakes.push(q);
      }
    }

    pQuizQuestions = shuffleArray(uniqueMistakes);
    pQuizIndex = 0;
    pQuizAnswered = false;
    pQuizCorrectCount = 0;
    pQuizMistakes = [];
    lastPSelectedWord = null;
    lastPAnswerCorrect = false;

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
    }

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderParonymsQuizTab();
  }

  function answerPQuestion(selectedWord) {
    if (pQuizAnswered) return;

    const current = pQuizQuestions[pQuizIndex];
    if (!current) return;

    pQuizAnswered = true;
    lastPSelectedWord = selectedWord;
    const isCorrect = selectedWord.toLowerCase() === current.correct.toLowerCase();
    lastPAnswerCorrect = isCorrect;

    if (isCorrect) {
      pQuizCorrectCount++;
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
      }
    } else {
      const key = current.id !== undefined ? String(current.id) : (current.sentence || "").trim().toLowerCase();
      if (!pQuizMistakes.some(m => (m.id !== undefined ? String(m.id) : (m.sentence || "").trim().toLowerCase()) === key)) {
        pQuizMistakes.push(current);
      }
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
      }
    }

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderPQuizQuestion();
  }

  function nextPQuestion() {
    pQuizIndex++;
    pQuizAnswered = false;
    lastPSelectedWord = null;
    lastPAnswerCorrect = false;

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderParonymsQuizTab();
  }

  function resetPQuiz() {
    pQuizQuestions = [];
    pQuizIndex = 0;
    pQuizAnswered = false;
    pQuizCorrectCount = 0;
    pQuizMistakes = [];
    lastPSelectedWord = null;
    lastPAnswerCorrect = false;
    renderEge();
  }

  function savePMistakes(mistakes) {
    try {
      const seen = new Set();
      const unique = [];
      for (const m of (mistakes || [])) {
        const key = m && m.id !== undefined ? String(m.id) : (m && m.sentence ? m.sentence.trim().toLowerCase() : "");
        if (key && !seen.has(key)) {
          seen.add(key);
          unique.push(m);
        }
      }
      localStorage.setItem("ege_task5_mistakes", JSON.stringify(unique));
    } catch (e) {}
  }

  function getStoredPMistakes() {
    try {
      const raw = localStorage.getItem("ege_task5_mistakes");
      const list = raw ? JSON.parse(raw) : [];
      const seen = new Set();
      const unique = [];
      for (const m of list) {
        const key = m && m.id !== undefined ? String(m.id) : (m && m.sentence ? m.sentence.trim().toLowerCase() : "");
        if (key && !seen.has(key)) {
          seen.add(key);
          unique.push(m);
        }
      }
      return unique;
    } catch (e) {
      return [];
    }
  }

  // ==============================================================================
  // РАЗДЕЛ ЗАДАНИЯ 4: ОРФОЭПИЯ / УДАРЕНИЯ (СЛОВАРЬ + ТРЕНАЖЕР)
  // ==============================================================================

  function renderDictTab() {
    const query = dictSearchQuery.toLowerCase().trim();
    const filtered = (EGE_DATA.task4_words || []).filter(item => {
      const matchesPos = currentPosFilter === "all" || item.pos === currentPosFilter;
      const matchesQuery = !query || item.word.toLowerCase().includes(query) || (item.note && item.note.toLowerCase().includes(query));
      return matchesPos && matchesQuery;
    });

    const posFilters = [
      { id: "all", label: "Все" },
      { id: "noun", label: "Сущ." },
      { id: "adjective", label: "Прил." },
      { id: "verb", label: "Глаг." },
      { id: "participle", label: "Прич." },
      { id: "gerund", label: "Деепр." },
      { id: "adverb", label: "Нареч." }
    ];

    return `
      <div class="space-y-3">
        <!-- Search bar -->
        <div class="relative">
          <input
            type="text"
            value="${dictSearchQuery}"
            oninput="window.EGE.onDictSearch(this.value)"
            placeholder="Поиск слова по словарю ФИПИ..."
            class="w-full px-3.5 py-2.5 pl-9 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
          />
          <span class="absolute left-3 top-2.5 text-slate-400 text-xs">🔍</span>
          ${dictSearchQuery ? `
            <button onclick="window.EGE.onDictSearch('')" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 text-xs font-bold">✕</button>
          ` : ''}
        </div>

        <!-- Part of speech pills -->
        <div class="flex items-center gap-1 overflow-x-auto pb-1 no-scrollbar text-xs">
          ${posFilters.map(p => `
            <button onclick="window.EGE.setPosFilter('${p.id}')" class="px-2.5 py-1 rounded-xl text-[11px] font-bold whitespace-nowrap transition-all ${
              currentPosFilter === p.id
                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700'
            }">
              ${p.label}
            </button>
          `).join('')}
        </div>

        <!-- Words Count and Notice -->
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>Найдено слов: <b>${filtered.length}</b> из ${(EGE_DATA.task4_words || []).length}</span>
          <span class="text-emerald-600 font-bold">Официальный кодификатор</span>
        </div>

        <!-- Words List Grid -->
        <div class="grid grid-cols-1 gap-1.5 max-h-[55vh] overflow-y-auto pr-1">
          ${filtered.length === 0 ? `
            <div class="text-center py-10 theme-card rounded-2xl p-6 text-slate-400 text-xs space-y-2">
              <span class="text-3xl">🔍</span>
              <p>По запросу «${dictSearchQuery}» ничего не найдено</p>
            </div>
          ` : filtered.map(item => `
            <div class="theme-card rounded-xl p-2.5 bg-white dark:bg-slate-800 border border-slate-200/70 dark:border-slate-700 flex items-center justify-between gap-2 shadow-sm">
              <div>
                <span class="text-sm font-bold text-slate-900 dark:text-white tracking-wide">
                  ${highlightStressedWord(item.word)}
                </span>
                ${item.note ? `<p class="text-[11px] text-slate-400 mt-0.5">${item.note}</p>` : ''}
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300 font-medium whitespace-nowrap">
                ${EGE_DATA.partOfSpeechMap[item.pos] || ''}
              </span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  function highlightStressedWord(word) {
    return word.split("").map(ch => {
      if (RUSSIAN_VOWELS.includes(ch) && ch === ch.toUpperCase()) {
        return `<span class="text-blue-600 dark:text-blue-400 font-extrabold underline decoration-2 decoration-blue-500">${ch}</span>`;
      }
      return ch;
    }).join("");
  }

  function renderQuizTab() {
    if (quizWords.length === 0) {
      return renderQuizSetup();
    }
    if (quizIndex >= quizWords.length) {
      return renderQuizResults();
    }
    return renderQuizQuestion();
  }

  function renderQuizSetup() {
    const totalWords = (EGE_DATA.task4_words || []).length;
    const storedMistakes = getStoredMistakes();

    return `
      <div class="theme-card rounded-3xl p-5 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-4">
        <div class="text-center space-y-1.5">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white text-2xl flex items-center justify-center mx-auto shadow-md shadow-blue-500/25">
            🎯
          </div>
          <h3 class="text-sm font-black text-slate-900 dark:text-white">Тренажер: Ударения (Задание 4)</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">
            Нажимайте прямо на правильную ударную гласную букву в слове.
          </p>
        </div>

        <!-- Question count selection -->
        <div class="space-y-2">
          <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Количество слов:</span>
          <div class="grid grid-cols-4 gap-1.5">
            ${[10, 25, 50, 'all'].map(cnt => {
              const label = cnt === 'all' ? `Все (${totalWords})` : cnt;
              const isSelected = (quizTotal === cnt || (cnt === 'all' && quizTotal === totalWords));
              return `
                <button onclick="window.EGE.setQuizTotal(${cnt === 'all' ? totalWords : cnt})" class="py-2.5 rounded-xl font-bold text-xs transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25 ring-2 ring-blue-400'
                    : 'bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                }">
                  ${label}
                </button>
              `;
            }).join('')}
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-2 pt-2">
          <button onclick="window.EGE.startQuiz(false)" class="w-full py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] text-white font-extrabold text-sm shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2">
            <span>🚀 Начать тренировку</span>
          </button>

          ${storedMistakes.length > 0 ? `
            <button onclick="window.EGE.startMistakesQuiz()" class="w-full py-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-amber-700 dark:text-amber-300 font-bold text-xs hover:bg-amber-100 transition-all flex items-center justify-center gap-2">
              <span>⚠️ Повторить ошибки (${storedMistakes.length})</span>
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }

  function renderQuizQuestion() {
    const current = quizWords[quizIndex];
    if (!current) return renderQuizResults();

    const progressPercent = Math.round(((quizIndex + (quizAnswered ? 1 : 0)) / quizWords.length) * 100);
    const letters = current.word.split("");

    return `
      <div class="theme-card rounded-3xl p-5 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-4">
        <!-- Progress Header -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-500 dark:text-slate-400">Слово ${quizIndex + 1} из ${quizWords.length}</span>
            <div class="flex items-center gap-1.5">
              <span class="text-emerald-600 font-bold">✓ ${quizCorrectCount}</span>
              <span class="text-rose-500 font-bold">✗ ${quizMistakes.length}</span>
              <button onclick="window.EGE.resetQuiz()" class="text-slate-400 hover:text-slate-600 ml-1 text-xs">✕ Выйти</button>
            </div>
          </div>
          <div class="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
            <div class="h-full bg-blue-600 rounded-full transition-all duration-300" style="width: ${progressPercent}%"></div>
          </div>
        </div>

        <!-- Question Prompt -->
        <div class="text-center">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Нажмите на ударную гласную:</span>
        </div>

        <!-- Interactive Word Tiles -->
        <div class="flex items-center justify-center flex-wrap gap-1.5 py-4 select-none">
          ${letters.map((ch, idx) => {
            const isVowel = RUSSIAN_VOWELS.includes(ch);
            const isTargetStressed = ch === ch.toUpperCase() && isVowel;
            const lowerCh = ch.toLowerCase();

            if (!isVowel) {
              return `
                <span class="w-9 h-11 flex items-center justify-center text-xl font-bold text-slate-700 dark:text-slate-200">
                  ${lowerCh}
                </span>
              `;
            }

            let tileClass = "bg-slate-100 dark:bg-slate-700/70 text-slate-800 dark:text-slate-100 hover:bg-blue-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-600 cursor-pointer active:scale-95";
            if (quizAnswered) {
              if (isTargetStressed) {
                tileClass = "bg-emerald-500 text-white border-emerald-600 font-black shadow-md shadow-emerald-500/25 ring-2 ring-emerald-400";
              } else if (window._lastClickedVowelIdx === idx) {
                tileClass = "bg-rose-500 text-white border-rose-600 font-black ring-2 ring-rose-400 animate-shake";
              } else {
                tileClass = "bg-slate-100 dark:bg-slate-800 text-slate-400 opacity-60 cursor-default";
              }
            }

            return `
              <button
                ${quizAnswered ? 'disabled' : ''}
                onclick="window.EGE.answerQuestion(${idx}, ${isTargetStressed})"
                class="w-10 h-12 rounded-2xl border-2 font-black text-xl flex items-center justify-center transition-all ${tileClass}">
                ${lowerCh}
              </button>
            `;
          }).join('')}
        </div>

        <!-- Feedback -->
        ${quizAnswered ? `
          <div class="p-3.5 rounded-2xl ${window._lastAnswerCorrect ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40 text-emerald-800 dark:text-emerald-300' : 'bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-rose-800 dark:text-rose-300'} text-xs space-y-1 transition-all">
            <div class="flex items-center gap-2 font-bold text-sm">
              <span>${window._lastAnswerCorrect ? '🎉 Правильно!' : '❌ Ошибка!'}</span>
              <span>Правильно: <u>${current.word}</u></span>
            </div>
          </div>

          <button onclick="window.EGE.nextQuestion()" class="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-extrabold text-sm shadow-md shadow-blue-500/25 transition-all flex items-center justify-center gap-2">
            <span>Дальше ➜</span>
          </button>
        ` : ''}
      </div>
    `;
  }

  function renderQuizResults() {
    const total = quizWords.length;
    const percent = Math.round((quizCorrectCount / total) * 100);
    const hasMistakes = quizMistakes.length > 0;

    saveMistakes(quizMistakes);

    return `
      <div class="theme-card rounded-3xl p-6 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm text-center space-y-5">
        <div class="w-16 h-16 mx-auto rounded-3xl bg-gradient-to-tr ${percent >= 80 ? 'from-emerald-500 to-teal-500 shadow-emerald-500/25' : percent >= 50 ? 'from-amber-500 to-yellow-500 shadow-amber-500/25' : 'from-rose-500 to-orange-500 shadow-rose-500/25'} text-white text-3xl flex items-center justify-center shadow-lg">
          ${percent >= 80 ? '🏆' : percent >= 50 ? '👍' : '💪'}
        </div>

        <div class="space-y-1">
          <h3 class="text-lg font-black text-slate-900 dark:text-white">Тренировка завершена!</h3>
          <p class="text-xs text-slate-400">Результат: ${quizCorrectCount} из ${total} верных (${percent}%)</p>
        </div>

        <!-- Mistakes breakdown if any -->
        ${hasMistakes ? `
          <div class="text-left space-y-2 pt-2 border-t border-slate-100 dark:border-slate-700">
            <span class="text-xs font-bold text-rose-500">Слова с ошибками (${quizMistakes.length}):</span>
            <div class="grid grid-cols-2 gap-1.5 max-h-48 overflow-y-auto pr-1">
              ${quizMistakes.map(m => `
                <div class="p-2 rounded-xl bg-rose-50/70 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 text-xs font-bold text-rose-700 dark:text-rose-300 truncate">
                  ${m.word}
                </div>
              `).join('')}
            </div>
          </div>
        ` : `
          <div class="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 text-xs font-bold">
            🌟 Отличный результат! Все слова отвечены правильно!
          </div>
        `}

        <div class="space-y-2 pt-2">
          ${hasMistakes ? `
            <button onclick="window.EGE.startMistakesQuiz()" class="w-full py-3 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 active:scale-[0.98] text-white font-extrabold text-xs shadow-md shadow-amber-500/25 transition-all flex items-center justify-center gap-2">
              <span>🔄 Отработать только ошибки (${quizMistakes.length})</span>
            </button>
          ` : ''}

          <button onclick="window.EGE.resetQuiz()" class="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-extrabold text-xs shadow-md shadow-blue-500/25 transition-all">
            <span>🎯 Начать новую тренировку</span>
          </button>
        </div>
      </div>
    `;
  }

  function setPosFilter(pos) {
    currentPosFilter = pos;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderDictTab();
  }

  function onDictSearch(query) {
    dictSearchQuery = query;
    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderDictTab();
  }

  function setQuizTotal(total) {
    quizTotal = total;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.selectionChanged();
    }
    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderQuizTab();
  }

  function startQuiz(isMistakes = false) {
    let pool = EGE_DATA.task4_words || [];
    if (pool.length === 0) return;

    // Shuffle pool using Fisher-Yates
    const shuffled = shuffleArray(pool);

    // Strict deduplication by lowercase word so no word ever repeats in one test
    const seenWords = new Set();
    const uniquePool = [];
    for (const item of shuffled) {
      const key = (item.word || "").toLowerCase();
      if (key && !seenWords.has(key)) {
        seenWords.add(key);
        uniquePool.push(item);
      }
    }

    const count = Math.min(quizTotal, uniquePool.length);
    quizWords = uniquePool.slice(0, count);

    quizIndex = 0;
    quizAnswered = false;
    quizCorrectCount = 0;
    quizMistakes = [];
    window._lastClickedVowelIdx = null;
    window._lastAnswerCorrect = false;

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
    }

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderQuizTab();
  }

  function startMistakesQuiz() {
    const mistakes = getStoredMistakes();
    if (!mistakes || mistakes.length === 0) return;

    // Deduplicate mistakes by lowercase word
    const seen = new Set();
    const uniqueMistakes = [];
    for (const m of mistakes) {
      const key = (m && m.word ? m.word : "").toLowerCase();
      if (key && !seen.has(key)) {
        seen.add(key);
        uniqueMistakes.push(m);
      }
    }

    quizWords = shuffleArray(uniqueMistakes);
    quizIndex = 0;
    quizAnswered = false;
    quizCorrectCount = 0;
    quizMistakes = [];
    window._lastClickedVowelIdx = null;
    window._lastAnswerCorrect = false;

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
    }

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderQuizTab();
  }

  function answerQuestion(vowelIdx, isCorrect) {
    if (quizAnswered) return;

    const currentWord = quizWords[quizIndex];
    if (!currentWord) return;

    quizAnswered = true;
    window._lastClickedVowelIdx = vowelIdx;
    window._lastAnswerCorrect = isCorrect;

    if (isCorrect) {
      quizCorrectCount++;
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
      }
    } else {
      if (!quizMistakes.some(m => m.word.toLowerCase() === currentWord.word.toLowerCase())) {
        quizMistakes.push(currentWord);
      }
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
      }
    }

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderQuizQuestion();
  }

  function nextQuestion() {
    quizIndex++;
    quizAnswered = false;
    window._lastClickedVowelIdx = null;
    window._lastAnswerCorrect = false;

    const subContainer = document.getElementById("ege-subtab-container");
    if (subContainer) subContainer.innerHTML = renderQuizTab();
  }

  function resetQuiz() {
    quizWords = [];
    quizIndex = 0;
    quizAnswered = false;
    quizCorrectCount = 0;
    quizMistakes = [];
    renderEge();
  }

  function saveMistakes(mistakes) {
    try {
      const seen = new Set();
      const unique = [];
      for (const m of (mistakes || [])) {
        if (!m || !m.word) continue;
        const key = m.word.toLowerCase();
        if (!seen.has(key)) {
          seen.add(key);
          unique.push(m);
        }
      }
      localStorage.setItem("ege_task4_mistakes", JSON.stringify(unique));
    } catch (e) {}
  }

  function getStoredMistakes() {
    try {
      const raw = localStorage.getItem("ege_task4_mistakes");
      const list = raw ? JSON.parse(raw) : [];
      const seen = new Set();
      const unique = [];
      for (const m of list) {
        if (!m || !m.word) continue;
        const key = m.word.toLowerCase();
        if (!seen.has(key)) {
          seen.add(key);
          unique.push(m);
        }
      }
      return unique;
    } catch (e) {
      return [];
    }
  }

  window.EGE = {
    init: initEge,
    selectSubject: selectSubject,
    selectTask: selectTask,
    setSubTab: setSubTab,
    // Task 4 (Ударения)
    setPosFilter: setPosFilter,
    onDictSearch: onDictSearch,
    setQuizTotal: setQuizTotal,
    startQuiz: startQuiz,
    startMistakesQuiz: startMistakesQuiz,
    answerQuestion: answerQuestion,
    nextQuestion: nextQuestion,
    resetQuiz: resetQuiz,
    // Task 5 (Паронимы)
    setPLetterFilter: setPLetterFilter,
    onParonymSearch: onParonymSearch,
    setPQuizTotal: setPQuizTotal,
    startPQuiz: startPQuiz,
    startPMistakesQuiz: startPMistakesQuiz,
    answerPQuestion: answerPQuestion,
    nextPQuestion: nextPQuestion,
    resetPQuiz: resetPQuiz,
    // Task 18 (Параметры)
    selectMath18Topic: selectMath18Topic,
    onMath18Search: onMath18Search,
    selectMath18Task: selectMath18Task,
    nextMath18Task: nextMath18Task,
    prevMath18Task: prevMath18Task,
    randomMath18Task: randomMath18Task,
    toggleMath18Solution: toggleMath18Solution,
    viewPhoto: viewPhoto
  };
})();
