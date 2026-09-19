import { NatAPI } from '../api.js';
import { store } from '../state.js';

const LABELS = {
  workers: '👷 Работники',
  automation: '🤖 Автоматизация',
  technology: '🧠 Технологии',
  level: '⬆️ Уровень завода',
};

export async function renderUpgrades(container, showToast) {
  let factories = store.factories || [];
  try {
    const data = await NatAPI.getProductionStatus();
    if (Array.isArray(data?.factories)) {
      factories = data.factories;
      store.updateCompany({ factories });
    }
  } catch (error) {
    console.warn('Could not refresh factories for upgrades:', error);
  }

  container.innerHTML = `<div class="space-y-4 max-w-md mx-auto p-4 pb-24">
    <div>
      <h2 class="text-xl font-black">Прокачка производств</h2>
      <p class="text-xs text-slate-500">Цена, требования и эффект приходят только с сервера</p>
    </div>
    <div class="space-y-3">
      ${factories.map(factoryCard).join('') || `<div class="glass-card rounded-2xl p-6 text-center text-sm text-slate-500 space-y-3"><p>Сначала постройте предприятие в каталоге.</p><button class="upgrade-help-btn rounded-xl bg-blue-600 px-3 py-2 text-xs font-bold text-white">Как начать прокачку</button></div>`}
    </div>
  </div>`;

  container.querySelectorAll('.upgrade-btn').forEach(btn => btn.addEventListener('click', async () => {
    if (btn.disabled) return;
    btn.disabled = true;
    try {
      const result = await NatAPI.upgradeFactory(Number(btn.dataset.factoryId), btn.dataset.type);
      showToast(`Улучшение применено. Списано ${Math.round(result.cost_paid).toLocaleString('ru-RU')} cash`, 'success');
      const refreshed = await NatAPI.getMyCompany();
      store.setCompany(refreshed);
      await renderUpgrades(container, showToast);
    } catch (error) {
      showToast(error.message, 'error');
      btn.disabled = false;
    }
  }));

  container.querySelectorAll('.upgrade-help-btn').forEach(btn => btn.addEventListener('click', () => {
    window.NatApp?.navigateTo('help');
  }));
}

function factoryCard(factory) {
  const upgrades = Array.isArray(factory.upgrade_options) ? factory.upgrade_options : [];
  return `<div class="glass-card rounded-2xl p-4 space-y-3" data-factory-id="${factory.id}">
    <div class="flex justify-between items-center">
      <div>
        <div class="text-sm font-black text-slate-900 dark:text-white">${factory.name || factory.building_type}</div>
        <div class="text-[10px] text-slate-500">Ур. ${factory.level || 1} · ${factory.specialization || ''}</div>
      </div>
      <span class="text-lg">⚙️</span>
    </div>
    <div class="grid grid-cols-2 gap-2">
      ${upgrades.map(u => upgradeCard(factory.id, u)).join('') || '<div class="col-span-2 text-xs text-slate-500">Сервер не вернул варианты прокачки.</div>'}
    </div>
  </div>`;
}

function upgradeCard(factoryId, u) {
  const title = LABELS[u.type] || u.type;
  const current = Number(u.current ?? u.current_level ?? 0);
  const next = Number(u.next ?? u.next_level ?? current);
  const cost = Number(u.cost || 0);
  const button = u.allowed
    ? `<button class="upgrade-btn w-full rounded-xl bg-blue-600 hover:bg-blue-500 text-white py-2 text-[11px] font-bold" data-factory-id="${factoryId}" data-type="${u.type}">Купить: ${cost.toLocaleString('ru-RU')} cash</button>`
    : `<div class="space-y-1"><button disabled class="w-full rounded-xl bg-slate-800/60 text-slate-500 py-2 text-[10px] font-bold cursor-not-allowed">${u.reason || 'Недоступно'}</button><button class="upgrade-help-btn w-full text-[10px] font-bold text-blue-600 dark:text-blue-300">Как выполнить условие?</button></div>`;

  return `<div class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 p-2.5 flex flex-col justify-between">
    <div>
      <div class="text-[11px] font-bold text-slate-800 dark:text-slate-100">${title}</div>
      <div class="text-[9px] text-emerald-600 dark:text-emerald-400 mt-0.5">${u.effect || ''}</div>
      <div class="font-mono text-[10px] text-slate-500 my-1.5">${current} ➔ <span class="font-bold text-slate-800 dark:text-white">${next}</span></div>
    </div>
    ${button}
  </div>`;
}
