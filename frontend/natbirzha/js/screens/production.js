import { NatAPI } from '../api.js';
import { store } from '../state.js';

// Canonical recipes: food_processing, mine_rare_lithium
const FACTORIES = [
  ['farm','🌾 Ферма'],['mine','⛏️ Рудник'],['smelter','🏭 Металлургический комбинат'],['oil_rig','🛢️ Нефтяная вышка'],
  ['hydro_solar','⚡ ГЭС/СЭС'],['logging_camp','🌲 Лесозаготовка'],['chem_plant','⚗️ Химзавод'],['machinery_plant','🤖 Машиностроительный завод'],
  ['refinery','🏗️ НПЗ'],['deep_mine','💎 Глубокий рудник'],['food_factory','🍞 Пищевой завод'],['sawmill','🪵 Лесопилка']
];

export async function renderProduction(container, showToast) {
  const data = await NatAPI.getProductionStatus().catch(() => ({ factories: [] }));
  if (data.factories) store.updateCompany({ factories: data.factories });
  const factories = data.factories || store.factories || [];
  const recipes = (await NatAPI.getRecipes().catch(() => ({ recipes: {} }))).recipes || {};
  container.innerHTML = `<div class="space-y-4 max-w-md mx-auto p-4 pb-24">
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-xl font-black">Заводы</h2>
        <p class="text-xs text-slate-500">Один клик запускает один реальный производственный цикл.</p>
      </div>
      <div class="flex gap-2">
        <button id="go-upgrades" class="px-3 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-100 text-xs font-bold">⚡ Прокачка</button>
        <button id="build" class="px-3 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold">➕ Завод</button>
      </div>
    </div>
    <div class="space-y-3">${factories.map(f => card(f, recipes)).join('') || empty()}</div>
    <div id="modal" class="fixed inset-0 z-50 hidden bg-black/60 items-center justify-center p-4"><div class="glass-card rounded-2xl p-5 w-full max-w-sm"><div class="flex justify-between mb-3"><b>Построить предприятие</b><button id="close">✕</button></div><div class="space-y-2 max-h-80 overflow-y-auto">${FACTORIES.map(([id,name]) => `<button data-build="${id}" class="build-btn w-full text-left p-3 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-bold">${name}</button>`).join('')}</div></div></div>
  </div>`;

  container.querySelector('#go-upgrades')?.addEventListener('click', () => {
    if (window.NatApp?.navigateTo) {
      window.NatApp.navigateTo('upgrades');
    }
  });

  container.querySelector('#build')?.addEventListener('click', () => { const m=container.querySelector('#modal'); m.classList.remove('hidden'); m.classList.add('flex'); });
  container.querySelector('#close')?.addEventListener('click', closeModal);
  container.querySelectorAll('.build-btn').forEach(b => b.addEventListener('click', async () => {
    try { b.disabled=true; await NatAPI.buildFactory(b.dataset.build); showToast('Завод построен', 'success'); await renderProduction(container, showToast); }
    catch(e){ showToast(e.message,'error'); } finally { b.disabled=false; }
  }));
  bindCycles(container, showToast, recipes);
}

function card(f, recipes) {
  const bType = f.building_type || f.factory_type;
  const list = Object.entries(recipes).filter(([,r]) => r.factory_type === bType);
  const running = Boolean(f.cycle_ready_at);
  const ready = running && new Date(f.cycle_ready_at).getTime() <= Date.now();
  return `<div class="glass-card rounded-2xl p-4 space-y-3" data-factory-id="${f.id}">
    <div class="flex justify-between"><div><div class="text-sm font-black">${f.name || bType}</div><div class="text-[10px] text-slate-500">${f.specialization} · уровень ${f.level}</div></div><div class="text-right text-[10px]">👷 ${f.workers || 10}<br>🤖 ${f.automation_level || 0}</div></div>
    <select class="recipe-select w-full p-2 rounded-lg border bg-transparent text-xs" ${running?'disabled':''}>${list.map(([id,r])=>`<option value="${id}" ${f.current_recipe===id?'selected':''}>${r.name}</option>`).join('')}</select>
    <div class="cycle-status text-xs font-mono text-center ${ready?'text-emerald-500':''}">${running ? (ready ? '✅ Цикл готов' : '⏳ Цикл выполняется') : '⭕ Готов к запуску'}</div>
    <button class="produce-btn w-full py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-bold" data-id="${f.id}">${ready?'📦 Забрать продукцию':running?'⏳ Обработка...':'▶️ Запустить цикл'}</button>
  </div>`;
}

function bindCycles(container, showToast, recipes) {
  container.querySelectorAll('.produce-btn').forEach(btn => btn.addEventListener('click', async () => {
    const card=btn.closest('[data-factory-id]'); const select=card.querySelector('.recipe-select');
    try { btn.disabled=true; const result=await NatAPI.triggerProduction(btn.dataset.id, select?.value); showToast(result.status==='running'?'Цикл запущен':'Цикл завершён','success'); await renderProduction(container,showToast); }
    catch(e){ showToast(e.message,'error'); btn.disabled=false; }
  }));
}
function closeModal(){ const m=document.getElementById('modal'); if(m){m.classList.add('hidden');m.classList.remove('flex');} }
function empty(){return '<div class="glass-card rounded-2xl p-8 text-center text-sm text-slate-500">Нет заводов.</div>'}
