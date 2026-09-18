import { NatAPI } from '../api.js';
import { store } from '../state.js';

const AVAILABLE_FACTORIES = [
  { type: 'smelter', name: 'Металлургический комбинат', cost: 5000, spec: 'metallurgist', tier: 1 },
  { type: 'aluminum_plant', name: 'Алюминиевый завод', cost: 8000, spec: 'metallurgist', tier: 2 },
  { type: 'thermal_plant', name: 'Угольная ТЭС', cost: 6000, spec: 'power_engineer', tier: 1 },
  { type: 'hydro_solar', name: 'ВИЭ / ГЭС электростанция', cost: 6000, spec: 'power_engineer', tier: 1 },
  { type: 'nuclear_plant', name: 'Атомная электростанция', cost: 25000, spec: 'power_engineer', tier: 3 },
  { type: 'oil_rig', name: 'Нефтяная вышка', cost: 5500, spec: 'oilman', tier: 1 },
  { type: 'refinery', name: 'НПЗ (Нефтепереработка)', cost: 7000, spec: 'oilman', tier: 2 },
  { type: 'chem_plant', name: 'Химический комбинат', cost: 5500, spec: 'chemist', tier: 1 },
  { type: 'polymer_plant', name: 'Завод полимеров', cost: 8500, spec: 'chemist', tier: 2 },
  { type: 'mine', name: 'Угольно-рудная шахта', cost: 5000, spec: 'miner', tier: 1 },
  { type: 'deep_mine', name: 'Глубокая шахта (литий/редкоземы)', cost: 9000, spec: 'miner', tier: 2 },
  { type: 'uranium_quarry', name: 'Урановый карьер', cost: 15000, spec: 'miner', tier: 3 },
  { type: 'farm', name: 'Агрокомплекс (ферма)', cost: 5000, spec: 'agrarian', tier: 1 },
  { type: 'food_factory', name: 'Пищевой комбинат', cost: 7000, spec: 'agrarian', tier: 2 },
  { type: 'logging_camp', name: 'Лесозаготовительный лагерь', cost: 5000, spec: 'forester', tier: 1 },
  { type: 'sawmill', name: 'Лесопильный комбинат', cost: 6500, spec: 'forester', tier: 2 },
  { type: 'machinery_plant', name: 'Машиностроительный завод', cost: 7500, spec: 'technoprom', tier: 1 },
  { type: 'electronics_fab', name: 'Фабрика электроники', cost: 8000, spec: 'technoprom', tier: 2 },
  { type: 'centrifuge', name: 'Газоцентрифужный завод', cost: 18000, spec: 'miner', tier: 3 },
  { type: 'defense_plant', name: 'Оборонный завод ВПК', cost: 30000, spec: 'technoprom', tier: 3 },
];

const RECIPES = {
  smelter: [
    { id: 'smelt_steel', name: 'Выплавка стали', in: '2 iron_ore + 1 coal + 2 energy', out: '1 steel', xp: 50 },
  ],
  aluminum_plant: [
    { id: 'smelt_aluminum', name: 'Электролиз алюминия', in: '2 bauxite + 1 minerals + 3.5 energy', out: '1 aluminum', xp: 60 },
  ],
  thermal_plant: [
    { id: 'generate_thermal', name: 'Генерация электроэнергии', in: '2 coal + 1 water', out: '25 energy', xp: 40 },
  ],
  hydro_solar: [
    { id: 'generate_solar_hydro', name: 'Бестопливная генерация (ВИЭ/ГЭС)', in: '0 сырья', out: '15 energy', xp: 35 },
  ],
  nuclear_plant: [
    { id: 'generate_nuclear', name: 'Ядерная генерация', in: '0.5 uranium_enriched + 3 water', out: '60 energy', xp: 70 },
  ],
  oil_rig: [
    { id: 'pump_oil_gas', name: 'Добыча нефти и газа', in: '2 grid_quota + 1 water', out: '3 oil_crude + 2 gas_natural', xp: 35 },
  ],
  refinery: [
    { id: 'refine_fuel', name: 'Переработка топлива', in: '2 oil_crude + 2 energy', out: '80 fuel_diesel', xp: 45 },
  ],
  chem_plant: [
    { id: 'synth_chem_fertilizer', name: 'Синтез удобрений и кислот', in: '1.5 minerals + 1.5 water + 2 energy', out: '2 basic_chem + 2 fertilizer', xp: 40 },
  ],
  polymer_plant: [
    { id: 'synth_plastics_catalyst', name: 'Синтез пластиков и катализаторов', in: '2 oil_crude + 1 basic_chem + 2 energy', out: '2 plastics + 1 catalyst', xp: 55 },
  ],
  mine: [
    { id: 'mine_coal_iron', name: 'Добыча угля и железной руды', in: '2 grid_quota + 1 water', out: '4 coal + 3 iron_ore + 2 minerals', xp: 35 },
  ],
  deep_mine: [
    { id: 'mine_deep_rare', name: 'Глубокая добыча лития и редкоземов', in: '3 grid_quota + 2 water', out: '2 lithium_raw + 1.5 rare_earths + 1 bauxite', xp: 45 },
  ],
  uranium_quarry: [
    { id: 'mine_uranium', name: 'Добыча урановой руды', in: '3 grid_quota + 2 water', out: '2 uranium_raw', xp: 50 },
  ],
  farm: [
    { id: 'farm_grain', name: 'Выращивание зерна', in: '1 water + 1 grid_quota', out: '5 grain + 2 bio_raw', xp: 30 },
  ],
  food_factory: [
    { id: 'process_food', name: 'Переработка продовольствия', in: '3 grain + 1 water + 1 energy', out: '5 food', xp: 35 },
  ],
  logging_camp: [
    { id: 'log_timber', name: 'Лесозаготовка', in: '1.5 grid_quota', out: '5 wood_raw', xp: 30 },
  ],
  sawmill: [
    { id: 'mill_lumber', name: 'Производство пиломатериалов', in: '3 wood_raw + 1.5 energy', out: '2 lumber + 1 cellulose', xp: 35 },
  ],
  machinery_plant: [
    { id: 'manufacture_machinery', name: 'Производство оборудования', in: '1.5 steel + 2 energy', out: '1 machinery', xp: 45 },
  ],
  electronics_fab: [
    { id: 'manufacture_electronics', name: 'Производство чипов и батарей', in: '0.5 rare_earths + 1 lithium_raw + 1 plastics + 3 energy', out: '1 electronics + 1 batteries', xp: 50 },
  ],
  centrifuge: [
    { id: 'enrich_uranium', name: 'Обогащение урана', in: '2 uranium_raw + 1 minerals + 3 grid_quota', out: '1 uranium_enriched', xp: 60 },
  ],
  defense_plant: [
    { id: 'manufacture_military', name: 'Производство военного снаряжения', in: '2 steel + 1 electronics + 1 machinery + 5 energy', out: '1 military_gear', xp: 70 },
  ],
};

export async function renderProduction(container, showToast) {
  let statusData = null;
  try {
    statusData = await NatAPI.getProductionStatus();
    store.updateCompany({ factories: statusData.factories, inventory: statusData.inventory });
  } catch (err) {
    console.error('Failed to fetch production status:', err);
  }

  const factories = statusData?.factories || store.factories || [];

  container.innerHTML = `
    <div class="space-y-4 max-w-md mx-auto p-4 pb-24">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-black text-slate-900 dark:text-white">Промышленные мощности</h2>
          <p class="text-xs text-slate-500">Заводы и единый движок производственных циклов</p>
        </div>
        <button
          id="open-build-modal-btn"
          class="px-3 py-2 rounded-xl bg-blue-600 text-white font-bold text-xs shadow-md shadow-blue-500/20 hover:bg-blue-700 active:scale-95 transition-all"
        >
          ➕ Построить завод
        </button>
      </div>

      <!-- Factory List -->
      <div class="space-y-3" id="factories-container">
        ${factories.length === 0 ? `
          <div class="glass-card rounded-2xl p-8 text-center space-y-3">
            <div class="text-4xl">🏗️</div>
            <div class="font-bold text-sm text-slate-700 dark:text-slate-200">У вас пока нет заводов</div>
            <div class="text-xs text-slate-400">Постройте первое промышленное предприятие, чтобы начать выпускать продукцию.</div>
          </div>
        ` : factories.map(f => {
          const recipes = RECIPES[f.factory_type] || [{ id: 'default_tick', name: 'Стандартный цикл', in: 'Сырьё', out: 'Продукция', xp: 30 }];
          return `
            <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3" data-factory-id="${f.id}">
              <div class="flex items-start justify-between">
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs font-bold font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      Tier ${f.tier || 1}
                    </span>
                    <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      ${f.is_active ? '● Работает' : '○ Остановлен'}
                    </span>
                  </div>
                  <h3 class="font-bold text-sm text-slate-900 dark:text-white mt-1 capitalize">
                    ${f.name || f.factory_type.replace(/_/g, ' ')}
                  </h3>
                </div>
                <div class="text-right text-[11px] text-slate-400 font-mono">
                  Износ: ${(f.degradation || 0).toFixed(1)}%
                </div>
              </div>

              <!-- Recipe selector and trigger -->
              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 space-y-2">
                <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Рецепт производства:</div>
                <select class="recipe-select w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-900 dark:text-white">
                  ${recipes.map(r => `
                    <option value="${r.id}" ${f.current_recipe === r.id ? 'selected' : ''}>
                      ${r.name} (${r.in} ➔ ${r.out})
                    </option>
                  `).join('')}
                </select>

                <button
                  class="produce-tick-btn w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-500/20 active:scale-98 transition-all flex items-center justify-center gap-1.5"
                  data-factory-id="${f.id}"
                >
                  ⚙️ Запустить рабочий цикл (Тик)
                </button>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>

    <!-- Modal for Building Factory -->
    <div id="build-modal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm hidden items-center justify-center p-4">
      <div class="glass-card rounded-2xl max-w-sm w-full p-5 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between">
          <h3 class="font-black text-slate-900 dark:text-white text-base">Строительство предприятия</h3>
          <button id="close-modal-btn" class="text-slate-400 hover:text-slate-600 dark:hover:text-white text-lg">✕</button>
        </div>
        <div class="space-y-2 max-h-80 overflow-y-auto pr-1">
          ${AVAILABLE_FACTORIES.map(item => `
            <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <div>
                <div class="font-bold text-xs text-slate-900 dark:text-white">${item.name}</div>
                <div class="text-[10px] text-slate-400 font-mono">${item.cost.toLocaleString()} cash</div>
              </div>
              <button
                class="build-item-btn px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs active:scale-95 transition-all"
                data-type="${item.type}"
                data-cost="${item.cost}"
              >
                Построить
              </button>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // Modal open/close
  const modal = container.querySelector('#build-modal');
  container.querySelector('#open-build-modal-btn')?.addEventListener('click', () => {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  });
  container.querySelector('#close-modal-btn')?.addEventListener('click', () => {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  });

  // Build item handler
  container.querySelectorAll('.build-item-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const type = btn.getAttribute('data-type');
      try {
        btn.disabled = true;
        btn.innerText = '...';
        await NatAPI.buildFactory(type);
        modal.classList.add('hidden');
        showToast('Завод успешно построен!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderProduction(container, showToast);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerText = 'Построить';
      }
    });
  });

  // Produce manual tick handlers
  container.querySelectorAll('.produce-tick-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const factoryId = btn.getAttribute('data-factory-id');
      const card = btn.closest('[data-factory-id]');
      const recipeSelect = card.querySelector('.recipe-select');
      const recipeId = recipeSelect.value;

      try {
        btn.disabled = true;
        btn.innerText = 'Выполнение цикла...';
        const result = await NatAPI.triggerProduction(factoryId, recipeId);
        showToast(result.message || 'Производственный цикл завершён!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderProduction(container, showToast);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerText = '⚙️ Запустить рабочий цикл (Тик)';
      }
    });
  });
}
