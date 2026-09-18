import { NatAPI } from '../api.js';
import { store } from '../state.js';
import { getItemInfo } from '../items.js';

export function renderOverview(container, showToast) {
  const company = store.company;
  if (!company) { container.innerHTML = '<div class="p-8 text-center text-xs text-slate-400">Загрузка данных компании...</div>'; return; }

  const inv = store.inventory || {};
  const items = Object.entries(inv).filter(([_, qty]) => Number(qty) > 0);

  const xpCurrent = company.xp || 0;
  const xpNext = (company.level || 1) * 150;
  const xpPercent = Math.min(100, Math.round((xpCurrent / xpNext) * 100));

  container.innerHTML = `
    <div class="space-y-4 max-w-md mx-auto p-4 pb-20">
      <!-- Corporate Header Card -->
      <div class="glass-card rounded-2xl p-4 shadow-sm relative overflow-hidden">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-mono font-bold text-xs tracking-wider">
                [${company.ticker}]
              </span>
              <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 capitalize">
                ${company.specialization}
              </span>
            </div>
            <h2 class="text-lg font-black text-slate-900 dark:text-white mt-1">
              ${company.name}
            </h2>
          </div>
          <div class="text-right">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
              company.is_public
                ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-700'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
            }">
              ${company.is_public ? '🏛️ ПАО (IPO)' : '🔒 Частная'}
            </span>
          </div>
        </div>

        <!-- Level & XP Bar -->
        <div class="mt-4 pt-3 border-t border-slate-200/60 dark:border-slate-800">
          <div class="flex justify-between text-xs font-semibold mb-1">
            <span class="text-slate-600 dark:text-slate-300">Уровень ${company.level || 1}</span>
            <span class="text-slate-400 font-mono">${xpCurrent} / ${xpNext} XP</span>
          </div>
          <div class="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500" style="width: ${xpPercent}%"></div>
          </div>
        </div>
      </div>

      <!-- Financial Balance Stats Grid -->
      <div class="grid grid-cols-2 gap-3">
        <div class="glass-card rounded-2xl p-4 shadow-sm">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400">Счёт компании</div>
          <div class="text-xl font-black text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            ${Number(company.cash || 0).toLocaleString('ru-RU', { maximumFractionDigits: 2 })}
          </div>
          <div class="text-[11px] text-slate-400 mt-0.5">cash (ликвидность)</div>
        </div>

        <div class="glass-card rounded-2xl p-4 shadow-sm">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400">Оценка NAV</div>
          <div class="text-xl font-black text-blue-600 dark:text-blue-400 mt-1 font-mono">
            ${Number(store.nav || company.cash || 0).toLocaleString('ru-RU', { maximumFractionDigits: 2 })}
          </div>
          <div class="text-[11px] text-slate-400 mt-0.5">активы + склады + кеш</div>
        </div>
      </div>

      <!-- Energy & Infrastructure Status -->
      <div class="glass-card rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">⚡</span>
            <div>
              <div class="text-xs font-bold text-slate-800 dark:text-white">Муниципальная энергосеть</div>
              <div class="text-[11px] text-slate-400">Базовый лимит: 10 МВт·ч за тик (3.0 cash / МВт·ч)</div>
            </div>
          </div>
          <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-1 rounded-lg">
            В норме
          </span>
        </div>
      </div>

      <!-- Warehouse / Inventory -->
      <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-base">📦</span>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white">Складские запасы</h3>
          </div>
          <span class="text-xs text-slate-400 font-mono">${items.length} поз.</span>
        </div>

        ${items.length === 0 ? `
          <div class="text-center py-6 text-slate-400 text-xs">
            Склад пуст. Закупайте сырьё на бирже или у NPC для запуска производства.
          </div>
        ` : `
          <div class="grid grid-cols-2 gap-2">
            ${items.map(([itemId, qty]) => {
              const info = getItemInfo(itemId);
              return `
              <div class="resource-pill p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between">
                <div class="flex items-center gap-2 min-w-0 pr-1">
                  <span class="text-base shrink-0">${info.icon}</span>
                  <div class="min-w-0">
                    <div class="text-xs font-bold text-slate-800 dark:text-white leading-tight truncate">${info.name}</div>
                    <div class="text-[10px] text-slate-400 font-mono">${info.unit}</div>
                  </div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-sm font-black font-mono text-slate-900 dark:text-white">
                    ${Number(qty).toLocaleString('ru-RU')}
                  </div>
                </div>
              </div>
            `;}).join('')}
          </div>
        `}
      </div>

      <!-- Territory Expansion -->
      <div class="glass-card rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-base">🗺️</span>
            <div>
              <div class="text-xs font-bold text-slate-800 dark:text-white">Территория</div>
              <div class="text-[11px] text-slate-400">${company.territory_tiles || 4} / ${company.max_territory || 20} тайлов</div>
            </div>
          </div>
          <button
            id="expand-territory-btn"
            class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs active:scale-95 transition-all"
          >
            🏗️ Расширить
          </button>
        </div>
      </div>

      <!-- Actions: Respec & Refresh -->
      <div class="pt-2 flex items-center justify-center gap-2">
        <button
          id="respec-btn"
          class="px-3 py-2 rounded-xl text-xs font-bold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 hover:bg-amber-100 transition-colors"
        >
          🔄 Сменить отрасль
        </button>
        <button
          id="refresh-btn"
          class="px-3 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
        >
          ⚡ Обновить NAV
        </button>
      </div>
    </div>
  `;

  // Attach refresh handler
  const refreshBtn = container.querySelector('#refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      try {
        refreshBtn.innerText = 'Обновление...';
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderOverview(container, showToast);
        showToast('Данные актуализированы', 'info');
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        refreshBtn.innerText = '⚡ Обновить NAV';
      }
    });
  }

  // Attach respec handler
  const respecBtn = container.querySelector('#respec-btn');
  if (respecBtn) {
    respecBtn.addEventListener('click', async () => {
      const specs = ['metallurgist', 'power_engineer', 'oilman', 'agrarian', 'chemist', 'technoprom', 'miner', 'forester'];
      const specPrompt = prompt(
        `Выберите новую специализацию:\n${specs.join(', ')}`,
        company.specialization
      );
      if (!specPrompt || specPrompt === company.specialization) return;
      const targetSpec = specPrompt.trim().toLowerCase();
      if (!specs.includes(targetSpec)) {
        showToast('Неизвестная специализация!', 'error');
        return;
      }
      try {
        respecBtn.disabled = true;
        respecBtn.innerText = 'Смена...';
        await NatAPI.respecCompany(targetSpec);
        showToast('Отрасль компании успешно изменена!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderOverview(container, showToast);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        respecBtn.disabled = false;
        respecBtn.innerText = '🔄 Сменить отрасль';
      }
    });
  }

  const expandBtn = container.querySelector('#expand-territory-btn');
  if (expandBtn) {
    expandBtn.addEventListener('click', async () => {
      try {
        expandBtn.innerText = 'Расширение...';
        expandBtn.disabled = true;
        const res = await NatAPI.expandTerritory();
        showToast(res.message || 'Территория расширена!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderOverview(container, showToast);
      } catch (err) {
        showToast(err.message || 'Ошибка расширения территории', 'error');
      } finally {
        expandBtn.disabled = false;
        expandBtn.innerText = '🏗️ Расширить';
      }
    });
  }
}
