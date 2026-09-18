import { NatAPI } from '../api.js';
import { store } from '../state.js';

const SPECIALIZATIONS = [
  { id: 'metallurgist', name: 'Металлургия', icon: '⚙️', desc: 'Добыча руды, выплавка чугуна, стали и сплавов' },
  { id: 'power_engineer', name: 'Энергетика', icon: '⚡', desc: 'Угольные, газовые и АЭС, генерация МВт·ч' },
  { id: 'oilman', name: 'Нефтегаз', icon: '🛢️', desc: 'Бурение, сырая нефть, бензин и полимеры' },
  { id: 'agrarian', name: 'Агропром', icon: '🌾', desc: 'Зерно, биоэтанол, фермы и продовольствие' },
  { id: 'chemist', name: 'Химия', icon: '🧪', desc: 'Удобрения, кислоты, реагенты и синтетика' },
  { id: 'technoprom', name: 'Технопром', icon: '🔌', desc: 'Оборудование, электроника, высокие технологии' },
  { id: 'miner', name: 'Горнодобыча', icon: '⛏️', desc: 'Уголь, руда, минералы, литий и редкоземы' },
  { id: 'forester', name: 'Лесопром', icon: '🌲', desc: 'Лесозаготовка, пиломатериалы и целлюлоза' },
];

export function renderOnboarding(container, showToast) {
  let selectedSpec = 'metallurgist';

  container.innerHTML = `
    <div class="max-w-md mx-auto p-4 space-y-6">
      <div class="text-center space-y-2">
        <div class="w-16 h-16 mx-auto rounded-3xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-amber-500 flex items-center justify-center text-white text-3xl shadow-xl shadow-indigo-500/25">
          🏛️
        </div>
        <h1 class="text-2xl font-black text-slate-900 dark:text-white">Основание Корпорации</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Зарегистрируйте предприятие на НАТБИРЖЕ и получите стартовый капитал 50,000 cash.
        </p>
      </div>

      <form id="create-company-form" class="space-y-4">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
            Название компании
          </label>
          <input
            type="text"
            id="company-name"
            required
            maxlength="64"
            placeholder="Например: ПАО «Северсталь»"
            class="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
            Биржевой тикер (3-5 букв)
          </label>
          <input
            type="text"
            id="company-ticker"
            required
            minlength="3"
            maxlength="5"
            placeholder="STEEL"
            class="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 uppercase font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
            Промышленная отрасль (Специализация)
          </label>
          <div class="grid grid-cols-2 gap-2" id="spec-picker">
            ${SPECIALIZATIONS.map(s => `
              <button
                type="button"
                data-spec="${s.id}"
                class="spec-btn p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                  s.id === selectedSpec
                    ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/40 ring-2 ring-blue-500/50'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300'
                }"
              >
                <div class="text-xl mb-1">${s.icon}</div>
                <div class="font-bold text-xs text-slate-900 dark:text-white leading-tight">${s.name}</div>
                <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">${s.desc}</div>
              </button>
            `).join('')}
          </div>
        </div>

        <button
          type="submit"
          id="submit-create-btn"
          class="w-full py-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-sm shadow-lg shadow-blue-500/30 hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] transition-all"
        >
          🚀 Зарегистрировать компанию (+50,000 cash)
        </button>
      </form>
    </div>
  `;

  // Spec selection
  const specButtons = container.querySelectorAll('.spec-btn');
  specButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      selectedSpec = btn.getAttribute('data-spec');
      specButtons.forEach(b => {
        b.classList.remove('border-blue-500', 'bg-blue-50/50', 'dark:bg-blue-950/40', 'ring-2', 'ring-blue-500/50');
        b.classList.add('border-slate-200', 'dark:border-slate-800');
      });
      btn.classList.remove('border-slate-200', 'dark:border-slate-800');
      btn.classList.add('border-blue-500', 'bg-blue-50/50', 'dark:bg-blue-950/40', 'ring-2', 'ring-blue-500/50');
    });
  });

  // Form submit
  const form = container.querySelector('#create-company-form');
  const submitBtn = container.querySelector('#submit-create-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const nameInput = container.querySelector('#company-name');
    const tickerInput = container.querySelector('#company-ticker');
    const name = nameInput.value.trim();
    const ticker = tickerInput.value.trim().toUpperCase();

    if (!name || !ticker) {
      showToast('Заполните все поля!', 'error');
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerText = 'Создание...';
      const company = await NatAPI.createCompany({
        name,
        ticker,
        specialization: selectedSpec,
        territory_hex: 'NORTH_INDUSTRIAL_HEX_1',
      });
      let fullCompany = company;
      try {
        fullCompany = await NatAPI.getMyCompany();
      } catch (_) {}
      store.setCompany(fullCompany);
      store.setTab('overview');
      showToast(`Корпорация «${name}» успешно создана!`, 'success');
      document.getElementById('bottom-nav')?.classList.remove('hidden');
      document.getElementById('header-stats')?.classList.remove('hidden');
      if (typeof window !== 'undefined' && window.NatApp?.renderCurrentScreen) {
        window.NatApp.renderCurrentScreen();
      }
      setTimeout(() => window.location.reload(), 600);
    } catch (err) {
      showToast(err.message || 'Ошибка создания компании', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = '🚀 Зарегистрировать компанию (+50,000 cash)';
    }
  });
}
