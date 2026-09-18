import { NatAPI } from '../api.js';
import { store } from '../state.js';
import { getItemInfo } from '../items.js';
import { openCatalogModal } from './catalog.js';

// Canonical recipes: food_processing, mine_rare_lithium

function parseDateMs(dateStr) {
  if (!dateStr) return 0;
  const normalized = typeof dateStr === 'string' ? dateStr.replace(' ', 'T') : dateStr;
  const time = new Date(normalized).getTime();
  return isNaN(time) ? 0 : time;
}

export async function renderProduction(container, showToast) {
  let factories = (store.factories && store.factories.length > 0) ? store.factories : [];
  try {
    const data = await NatAPI.getProductionStatus();
    if (data && Array.isArray(data.factories) && data.factories.length > 0) {
      factories = data.factories;
      store.updateCompany({ factories: data.factories });
    }
  } catch (e) {
    console.warn('Could not fetch fresh factories, using cached state:', e);
  }

  const recipes = (await NatAPI.getRecipes().catch(() => ({ recipes: {} }))).recipes || {};
  container.innerHTML = `<div class="space-y-4 max-w-md mx-auto p-4 pb-24">
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-xl font-black">Заводы</h2>
        <p class="text-xs text-slate-500">Производственные комплексы вашей компании</p>
      </div>
      <div class="flex gap-2">
        <button id="go-upgrades" class="px-3 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-100 text-xs font-bold">⚡ Прокачка</button>
        <button id="build" class="px-3 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold shadow-lg shadow-blue-600/30">➕ Каталог (48)</button>
      </div>
    </div>
    <div class="space-y-3">${factories.map(f => card(f, recipes)).join('') || empty()}</div>
  </div>`;

  container.querySelector('#go-upgrades')?.addEventListener('click', () => {
    if (window.NatApp?.navigateTo) {
      window.NatApp.navigateTo('upgrades');
    }
  });

  container.querySelector('#build')?.addEventListener('click', () => {
    openCatalogModal(showToast, async () => {
      await renderProduction(container, showToast);
    });
  });

  bindCycles(container, showToast, recipes);
}

function formatRecipeReqs(recipe) {
  if (!recipe) return '';
  const inList = Object.entries(recipe.inputs || {}).map(([k, v]) => {
    const info = getItemInfo(k);
    return `${v} ${info.unit} ${info.name}`;
  }).join(', ');
  const outList = Object.entries(recipe.outputs || {}).map(([k, v]) => {
    const info = getItemInfo(k);
    return `+${v} ${info.unit} ${info.name}`;
  }).join(', ');
  return `<div class="text-[10px] text-slate-400 mt-1">📥 ${inList || 'Без затрат'} ➔ 📤 ${outList}</div>`;
}

function card(f, recipes) {
  const bType = f.building_type || f.factory_type;
  const list = Object.entries(recipes).filter(([,r]) => r.factory_type === bType);
  const running = Boolean(f.cycle_ready_at || f.is_running);
  const remSec = typeof f.remaining_seconds === 'number'
    ? f.remaining_seconds
    : (f.cycle_ready_at ? Math.max(0, Math.ceil((parseDateMs(f.cycle_ready_at) - Date.now()) / 1000)) : 0);
  const ready = running && (Boolean(f.is_ready) || remSec <= 0);
  const readyAtMs = running && !ready ? (Date.now() + remSec * 1000) : 0;
  const selRecipeId = f.current_recipe || (list[0] ? list[0][0] : null);
  const curRecipe = selRecipeId ? recipes[selRecipeId] : null;
  const isOwn = (f.specialization === store.company?.specialization) || (f.efficiency >= 0.99);

  return `<div class="glass-card rounded-2xl p-4 space-y-3" data-factory-id="${f.id}">
    <div class="flex justify-between items-start">
      <div>
        <div class="text-sm font-black flex items-center gap-1.5">
          <span>${f.name || bType}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded ${isOwn ? 'bg-amber-500/20 text-amber-300 font-bold' : 'bg-slate-700 text-slate-400 font-medium'}">
            ${isOwn ? '🌟 100%' : '⚠️ 10%'}
          </span>
        </div>
        <div class="text-[10px] text-slate-500">${f.specialization || ''} · уровень ${f.level || 1}</div>
      </div>
      <div class="text-right text-[10px] text-slate-400">👷 ${f.workers || 10} · 🤖 ${f.automation_level || 0}</div>
    </div>
    <div>
      <select class="recipe-select w-full p-2 rounded-lg border bg-transparent text-xs" ${running && !ready ? 'disabled' : ''}>
        ${list.map(([id,r])=>`<option value="${id}" ${selRecipeId===id?'selected':''}>${r.name}</option>`).join('')}
      </select>
      <div class="recipe-reqs">${formatRecipeReqs(curRecipe)}</div>
    </div>
    <div class="cycle-status text-xs font-mono text-center ${ready ? 'text-emerald-500 font-bold' : (running ? 'text-amber-500' : 'text-slate-400')}" data-ready-ms="${running && !ready ? readyAtMs : 0}">
      ${ready ? '✅ Продукция готова к сбору' : (running ? '⏳ Цикл в процессе...' : '⭕ Готов к запуску')}
    </div>
    <button class="produce-btn w-full py-2.5 rounded-xl ${ready ? 'bg-emerald-600 shadow-lg shadow-emerald-600/30' : (running ? 'bg-slate-600 cursor-not-allowed opacity-80' : 'bg-emerald-600')} text-white text-xs font-bold" data-id="${f.id}" ${running && !ready ? 'disabled' : ''}>
      ${ready ? '📦 Забрать продукцию' : (running ? '⏳ Выполняется...' : '▶️ Запустить цикл')}
    </button>
  </div>`;
}

let cycleInterval = null;

function bindCycles(container, showToast, recipes) {
  if (cycleInterval) clearInterval(cycleInterval);

  cycleInterval = setInterval(() => {
    const now = Date.now();
    let needsRerender = false;
    let hasActiveCountdown = false;

    container.querySelectorAll('.cycle-status[data-ready-ms]').forEach(el => {
      const readyMs = parseInt(el.dataset.readyMs, 10);
      if (readyMs > 0) {
        hasActiveCountdown = true;
        if (now >= readyMs) {
          needsRerender = true;
        } else {
          const diff = Math.ceil((readyMs - now) / 1000);
          el.textContent = `⏳ Цикл в процессе (${diff} сек.)`;
        }
      }
    });

    if (needsRerender) {
      clearInterval(cycleInterval);
      renderProduction(container, showToast);
    } else if (!hasActiveCountdown) {
      clearInterval(cycleInterval);
    }
  }, 1000);

  container.querySelectorAll('.recipe-select').forEach(sel => {
    sel.addEventListener('change', () => {
      const card = sel.closest('[data-factory-id]');
      const reqsEl = card.querySelector('.recipe-reqs');
      if (reqsEl && recipes[sel.value]) {
        reqsEl.innerHTML = formatRecipeReqs(recipes[sel.value]);
      }
    });
  });

  container.querySelectorAll('.produce-btn').forEach(btn => btn.addEventListener('click', async () => {
    if (btn.disabled) return;
    const card = btn.closest('[data-factory-id]');
    const select = card.querySelector('.recipe-select');
    try {
      btn.disabled = true;
      const result = await NatAPI.triggerProduction(btn.dataset.id, select?.value);
      if (result.status === 'running') {
        showToast('Цикл запущен! Идет производство...', 'success');
      } else {
        showToast('Продукция успешно получена на склад!', 'success');
        NatAPI.getMyCompany().then(c => store.setCompany(c)).catch(() => {});
      }
      await renderProduction(container, showToast);
    } catch (e) {
      showToast(e.message, 'error');
      btn.disabled = false;
    }
  }));
}

function closeModal(){ const m=document.getElementById('modal'); if(m){m.classList.add('hidden');m.classList.remove('flex');} }
function empty(){return '<div class="glass-card rounded-2xl p-8 text-center text-sm text-slate-500">Нет заводов.</div>'}
