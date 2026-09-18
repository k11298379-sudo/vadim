import { NatAPI } from '../api.js';
import { store } from '../state.js';

const LABELS = {
  workers: ['👷 Работники', 'Увеличивает производственную мощность'],
  automation: ['🤖 Автоматизация', 'Сокращает время цикла'],
  technology: ['🧠 Технологии', 'Повышает технологический уровень завода'],
  level: ['⬆️ Уровень завода', 'Увеличивает объём выпуска за цикл'],
};

function calcUpgrade(f, type) {
  const level = f.level || 1;
  const workers = f.workers || 10;
  const auto = f.automation_level || 0;
  const tech = f.technology_level || 0;

  if (type === 'workers') {
    const cost = Math.round(1200 * (level + Math.floor(workers / 10)));
    return { cur: `${workers} чел.`, next: `${workers + 10} чел.`, cost, effect: '+10 рабочих' };
  }
  if (type === 'automation') {
    const cost = Math.round(3000 * (auto + 1));
    return { cur: `Ур. ${auto}`, next: `Ур. ${auto + 1}`, cost, effect: '-10% времени цикла' };
  }
  if (type === 'technology') {
    const cost = Math.round(4500 * (tech + 1));
    return { cur: `Ур. ${tech}`, next: `Ур. ${tech + 1}`, cost, effect: '+1 тех. уровень' };
  }
  if (type === 'level') {
    const cost = Math.round(7000 * (level + 1));
    return { cur: `Ур. ${level}`, next: `Ур. ${level + 1}`, cost, effect: '+1x множитель выпуска' };
  }
  return { cur: '0', next: '1', cost: 1000, effect: '' };
}

export async function renderUpgrades(container, showToast) {
  let factories = (store.factories && store.factories.length > 0) ? store.factories : [];
  try {
    const data = await NatAPI.getProductionStatus();
    if (data && Array.isArray(data.factories) && data.factories.length > 0) {
      factories = data.factories;
      store.updateCompany({ factories: data.factories });
    }
  } catch (e) {
    console.warn('Could not fetch factories for upgrades, using cache:', e);
  }

  const company = store.company || {};
  const cash = company.cash || 0;
  const compLevel = company.level || 1;

  container.innerHTML = `<div class="space-y-4 max-w-md mx-auto p-4 pb-24">
    <div>
      <h2 class="text-xl font-black">Прокачка производств</h2>
      <p class="text-xs text-slate-500">Авторитетный расчёт стоимости и эффектов на сервере</p>
    </div>
    <div class="space-y-3">${factories.map(f => factoryCard(f, cash, compLevel)).join('') || '<div class="glass-card rounded-2xl p-6 text-center text-sm text-slate-500">Сначала постройте предприятие в каталоге.</div>'}</div>
  </div>`;

  container.querySelectorAll('.upgrade-btn:not([disabled])').forEach(btn => btn.addEventListener('click', async () => {
    btn.disabled = true;
    const factoryId = Number(btn.dataset.factoryId);
    const type = btn.dataset.type;
    try {
      const result = await NatAPI.upgradeFactory(factoryId, type);
      showToast(`Улучшение применено! Списано ${Math.round(result.cost_paid).toLocaleString('ru-RU')} cash`, 'success');
      const refreshed = await NatAPI.getMyCompany();
      store.setCompany(refreshed);
      await renderUpgrades(container, showToast);
    } catch (e) {
      showToast(e.message, 'error');
      btn.disabled = false;
    }
  }));
}

function factoryCard(f, userCash, compLevel) {
  const fLevel = f.level || 1;
  return `<div class="glass-card rounded-2xl p-4 space-y-3" data-factory-id="${f.id}">
    <div class="flex justify-between items-center">
      <div>
        <div class="text-sm font-black text-slate-900 dark:text-white">${f.name || f.building_type}</div>
        <div class="text-[10px] text-slate-500">Уровень здания: ${fLevel} · ${f.specialization || ''}</div>
      </div>
      <span class="text-lg">⚙️</span>
    </div>
    <div class="grid grid-cols-2 gap-2">
      ${Object.entries(LABELS).map(([type, [title, hint]]) => {
        const u = calcUpgrade(f, type);
        const canAfford = userCash >= u.cost;
        const levelLocked = (type === 'level' && fLevel >= compLevel);

        let btnHtml = '';
        if (levelLocked) {
          btnHtml = `<button disabled class="w-full rounded-xl bg-slate-800/60 text-slate-500 py-2 text-[10px] font-bold cursor-not-allowed">🔒 Нужен ур. компании ${fLevel + 1}</button>`;
        } else if (!canAfford) {
          btnHtml = `<button disabled class="w-full rounded-xl bg-slate-800/60 text-rose-400 py-2 text-[10px] font-bold cursor-not-allowed">Не хватает: ${u.cost.toLocaleString('ru-RU')} ₽</button>`;
        } else {
          btnHtml = `<button class="upgrade-btn w-full rounded-xl bg-blue-600 hover:bg-blue-500 text-white py-2 text-[11px] font-bold shadow-md shadow-blue-600/20 active:scale-95 transition-all" data-factory-id="${f.id}" data-type="${type}">
            Купить: ${u.cost.toLocaleString('ru-RU')} ₽
          </button>`;
        }

        return `<div class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 p-2.5 flex flex-col justify-between">
          <div>
            <div class="text-[11px] font-bold text-slate-800 dark:text-slate-100 leading-tight">${title}</div>
            <div class="text-[9px] text-emerald-600 dark:text-emerald-400 font-medium mt-0.5">${u.effect}</div>
            <div class="font-mono text-[10px] text-slate-500 my-1.5">${u.cur} ➔ <span class="font-bold text-slate-800 dark:text-white">${u.next}</span></div>
          </div>
          ${btnHtml}
        </div>`;
      }).join('')}
    </div>
  </div>`;
}
