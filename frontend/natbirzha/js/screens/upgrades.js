import { NatAPI } from '../api.js';
import { store } from '../state.js';

const LABELS = {
  workers: ['👷 Работники', 'Увеличивает производственную мощность'],
  automation: ['🤖 Автоматизация', 'Сокращает время цикла'],
  technology: ['🧠 Технологии', 'Повышает технологический уровень завода'],
  level: ['⬆️ Уровень завода', 'Увеличивает объём выпуска за цикл'],
};

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
  container.innerHTML = `<div class="space-y-4 max-w-md mx-auto p-4 pb-24">
    <div><h2 class="text-xl font-black">Прокачка заводов</h2><p class="text-xs text-slate-500">Каждое улучшение покупается отдельно и применяется сервером.</p></div>
    <div class="space-y-3">${factories.map(f => factoryCard(f)).join('') || '<div class="glass-card rounded-2xl p-6 text-center text-sm text-slate-500">Сначала постройте завод.</div>'}</div>
  </div>`;
  container.querySelectorAll('.upgrade-btn').forEach(btn => btn.addEventListener('click', async () => {
    btn.disabled = true;
    const factoryId = Number(btn.dataset.factoryId);
    const type = btn.dataset.type;
    try {
      const result = await NatAPI.upgradeFactory(factoryId, type);
      showToast(`Улучшение применено. Списано ${result.cost_paid.toLocaleString('ru-RU')} cash`, 'success');
      const company = await NatAPI.getMyCompany();
      store.setCompany(company);
      await renderUpgrades(container, showToast);
    } catch (e) { showToast(e.message, 'error'); }
    finally { btn.disabled = false; }
  }));
}

function factoryCard(f) {
  const values = { workers: f.workers || 10, automation: f.automation_level || 0, technology: f.technology_level || 0, level: f.level || 1 };
  return `<div class="glass-card rounded-2xl p-4 space-y-3">
    <div class="flex justify-between"><div><b>${f.name || f.building_type}</b><div class="text-[10px] text-slate-500">Уровень ${values.level}</div></div><span>⚙️</span></div>
    <div class="grid grid-cols-2 gap-2">${Object.entries(LABELS).map(([type, [title, hint]]) => `<div class="rounded-xl border border-slate-200 dark:border-slate-700 p-3">
      <div class="text-xs font-bold">${title}</div><div class="text-[10px] text-slate-500 mb-2">${hint}</div><div class="font-mono text-xs mb-2">${values[type]}</div>
      <button class="upgrade-btn w-full rounded-lg bg-blue-600 text-white py-2 text-[11px] font-bold" data-factory-id="${f.id}" data-type="${type}">Улучшить</button>
    </div>`).join('')}</div>
  </div>`;
}
