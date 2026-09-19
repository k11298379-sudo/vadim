import { NatAPI } from '../api.js';

let activeTab = 'overview';
const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));

export async function renderCreator(container, showToast) {
  container.innerHTML = `
    <div class="space-y-4 max-w-md mx-auto p-4 pb-24 text-slate-100">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-black text-amber-400 flex items-center gap-2">
            <span>👑</span> Панель Создателя
          </h2>
          <p class="text-[11px] text-slate-400">Государственное управление и модерация рынка</p>
        </div>
        <button id="refresh-creator-btn" class="p-2 rounded-xl bg-slate-800 border border-slate-700 hover:bg-slate-700 text-xs">
          🔄
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex gap-1 overflow-x-auto pb-1 text-xs font-bold scrollbar-none">
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'overview' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="overview">🏛️ Казна</button>
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'market' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="market">⚖️ Модерация</button>
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'bonds' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="bonds">📜 Облигации</button>
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'tournaments' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="tournaments">⚔️ Турниры</button>
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'players' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="players">👥 Игроки</button>
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'premium' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="premium">💎 PVC</button>
        <button class="creator-tab-btn px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${activeTab === 'audit' ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-800/80 text-slate-300'}" data-tab="audit">📋 Аудит</button>
      </div>

      <div id="creator-tab-content" class="space-y-3">
        <div class="glass-card rounded-2xl p-6 text-center text-xs text-slate-400">Загрузка данных...</div>
      </div>
    </div>
  `;

  // Bind tab switching
  container.querySelectorAll('.creator-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab;
      renderCreator(container, showToast);
    });
  });

  const refreshBtn = container.querySelector('#refresh-creator-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => renderCreator(container, showToast));
  }

  const contentArea = container.querySelector('#creator-tab-content');
  if (!contentArea) return;

  try {
    if (activeTab === 'overview') {
      await loadOverviewTab(contentArea, showToast);
    } else if (activeTab === 'market') {
      await loadMarketTab(contentArea, showToast);
    } else if (activeTab === 'bonds') {
      await loadBondsTab(contentArea, showToast);
    } else if (activeTab === 'tournaments') {
      await loadTournamentsTab(contentArea, showToast);
    } else if (activeTab === 'players') {
      await loadPlayersTab(contentArea, showToast);
    } else if (activeTab === 'premium') {
      await loadPremiumLedgerTab(contentArea);
    } else if (activeTab === 'audit') {
      await loadAuditTab(contentArea, showToast);
    }
  } catch (err) {
    contentArea.innerHTML = `
      <div class="glass-card rounded-2xl p-4 border border-rose-500/30 bg-rose-950/20 text-center">
        <p class="text-rose-400 text-xs font-bold">${err.message || 'Ошибка загрузки данных администратора'}</p>
      </div>
    `;
  }
}

async function loadPlayersTab(el, showToast) {
  let search = '';
  let sort = 'last_activity_at';
  let page = 1;
  async function reload() {
    const data = await NatAPI.getCreatorPlayers({ search, sort, page });
    const pages = Math.max(1, Math.ceil(data.total / data.page_size));
    el.innerHTML = `<div class="space-y-3"><div class="glass-card rounded-2xl p-3 space-y-2"><div class="text-xs font-bold text-amber-400 uppercase">Список игроков</div><form id="creator-player-filter" class="flex gap-2"><input id="creator-player-search" value="${escapeHtml(search)}" class="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-xs text-white" placeholder="Компания или Telegram"><select id="creator-player-sort" class="rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-[10px] text-white"><option value="last_activity_at" ${sort === 'last_activity_at' ? 'selected' : ''}>Активность</option><option value="assets" ${sort === 'assets' ? 'selected' : ''}>Активы</option><option value="level" ${sort === 'level' ? 'selected' : ''}>Уровень</option><option value="army" ${sort === 'army' ? 'selected' : ''}>Армия</option><option value="military_rating" ${sort === 'military_rating' ? 'selected' : ''}>Рейтинг</option><option value="pvc_balance" ${sort === 'pvc_balance' ? 'selected' : ''}>PVC</option></select><button class="rounded-lg bg-amber-500 px-3 text-xs font-black text-slate-950">Найти</button></form><div class="text-[10px] text-slate-500">${data.total} компаний · стр. ${data.page}/${pages}</div></div><div class="space-y-2">${data.players.map(player => `<div class="glass-card rounded-2xl p-3 text-[10px]"><div class="flex justify-between gap-2"><div class="min-w-0"><div class="truncate text-xs font-black text-white">${escapeHtml(player.company_name)}</div><div class="truncate text-slate-400">${escapeHtml(player.telegram_name || player.telegram_username || 'Telegram не указан')} · ур. ${player.level}</div></div><div class="text-right font-mono text-amber-400">${Math.round(player.assets).toLocaleString('ru-RU')}<div class="text-[9px] text-slate-500">активы</div></div></div><div class="mt-2 grid grid-cols-3 gap-1.5 text-slate-400"><span>Cash <b class="text-slate-100">${Math.round(player.cash).toLocaleString('ru-RU')}</b></span><span>Земля <b class="text-slate-100">${player.territory}</b></span><span>Заводы <b class="text-slate-100">${player.factory_count}</b></span><span>Армия <b class="text-slate-100">${Math.round(player.army).toLocaleString('ru-RU')}</b></span><span>Рейтинг <b class="text-slate-100">${player.military_rating}</b></span><span>PVC <b class="text-amber-400">${player.pvc_balance}</b></span></div><div class="mt-1 text-[9px] text-slate-500">Последняя игровая активность: ${new Date(player.last_activity_at).toLocaleString('ru-RU')}</div></div>`).join('') || '<div class="glass-card rounded-2xl p-5 text-center text-xs text-slate-500">Ничего не найдено.</div>'}</div><div class="flex justify-between"><button id="creator-players-prev" class="rounded-lg bg-slate-800 px-3 py-2 text-xs disabled:opacity-40" ${page <= 1 ? 'disabled' : ''}>← Назад</button><button id="creator-players-next" class="rounded-lg bg-slate-800 px-3 py-2 text-xs disabled:opacity-40" ${page >= pages ? 'disabled' : ''}>Далее →</button></div></div>`;
    el.querySelector('#creator-player-filter')?.addEventListener('submit', async event => {
      event.preventDefault();
      search = el.querySelector('#creator-player-search').value.trim();
      sort = el.querySelector('#creator-player-sort').value;
      page = 1;
      try { await reload(); } catch (error) { showToast(error.message, 'error'); }
    });
    el.querySelector('#creator-players-prev')?.addEventListener('click', async () => { page -= 1; try { await reload(); } catch (error) { showToast(error.message, 'error'); } });
    el.querySelector('#creator-players-next')?.addEventListener('click', async () => { page += 1; try { await reload(); } catch (error) { showToast(error.message, 'error'); } });
  }
  await reload();
}

async function loadPremiumLedgerTab(el) {
  const data = await NatAPI.getCreatorPremiumLedger();
  const entries = data.entries || [];
  el.innerHTML = `
    <div class="glass-card rounded-2xl p-4 space-y-2">
      <div class="flex items-center justify-between gap-2"><div><div class="text-xs font-bold text-amber-400 uppercase">Журнал PVC</div><div class="text-[10px] text-slate-400">Неизменяемая история начислений и списаний Pivocoins.</div></div><span class="text-[10px] text-slate-500">${entries.length} операций</span></div>
      <div class="space-y-2 max-h-[31rem] overflow-y-auto">
        ${entries.map(entry => {
          const meta = entry.metadata && Object.keys(entry.metadata).length ? JSON.stringify(entry.metadata) : '—';
          const player = entry.telegram_name || entry.telegram_username || `Компания #${entry.company_id}`;
          return `<div class="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-[10px]"><div class="flex justify-between gap-3"><div><div class="font-bold text-slate-100">${escapeHtml(entry.company_name)} <span class="text-slate-500">· ${escapeHtml(player)}</span></div><div class="text-slate-400 mt-0.5">${escapeHtml(entry.reason)}</div></div><div class="font-mono font-black whitespace-nowrap ${entry.amount > 0 ? 'text-emerald-400' : 'text-rose-400'}">${entry.amount > 0 ? '+' : ''}${entry.amount} PVC</div></div><div class="mt-1 flex justify-between gap-2 text-slate-500"><span>Баланс ${entry.balance_before} → ${entry.balance_after}</span><span>${new Date(entry.created_at).toLocaleString('ru-RU')}</span></div><div class="mt-1 text-[9px] text-slate-500 break-all">${escapeHtml(meta)}</div></div>`;
        }).join('') || '<div class="py-4 text-center text-xs text-slate-500">Операций PVC пока нет.</div>'}
      </div>
    </div>
  `;
}

async function loadOverviewTab(el, showToast) {
  const data = await NatAPI.getCreatorOverview();
  el.innerHTML = `
    <div class="glass-card rounded-2xl p-4 border border-amber-500/30 bg-amber-950/20 space-y-2">
      <div class="text-xs text-amber-400 font-bold uppercase tracking-wider">Государственная Казна</div>
      <div class="text-2xl font-black text-white font-mono">${Math.round(data.treasury_cash).toLocaleString('ru-RU')} ₽</div>
      <div class="text-[10px] text-slate-400">Изолированный баланс государства (не смешивается с игроками)</div>
    </div>

    <div class="grid grid-cols-2 gap-2">
      <div class="glass-card rounded-xl p-3">
        <div class="text-[10px] text-slate-400">Компаний в игре</div>
        <div class="text-lg font-bold font-mono text-white">${data.total_companies}</div>
      </div>
      <div class="glass-card rounded-xl p-3">
        <div class="text-[10px] text-slate-400">Построено заводов</div>
        <div class="text-lg font-bold font-mono text-white">${data.total_factories}</div>
      </div>
      <div class="glass-card rounded-xl p-3">
        <div class="text-[10px] text-slate-400">Активных ордеров</div>
        <div class="text-lg font-bold font-mono text-emerald-400">${data.active_orders}</div>
      </div>
      <div class="glass-card rounded-xl p-3">
        <div class="text-[10px] text-slate-400">Ограничений цен</div>
        <div class="text-lg font-bold font-mono text-rose-400">${data.active_restrictions}</div>
      </div>
    </div>

    <div class="glass-card rounded-2xl p-4 space-y-1">
      <div class="text-xs text-slate-400 font-bold">Денежная масса в обороте</div>
      <div class="text-base font-black font-mono text-blue-400">${Math.round(data.cash_in_circulation).toLocaleString('ru-RU')} ₽</div>
    </div>
  `;
}

async function loadMarketTab(el, showToast) {
  const data = await NatAPI.getCreatorMarket();
  el.innerHTML = `
    <!-- Action buttons -->
    <div class="grid grid-cols-2 gap-2">
      <button id="open-warn-btn" class="py-2.5 px-3 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 text-xs font-bold transition-all">
        ⚠️ Предупреждение
      </button>
      <button id="open-restr-btn" class="py-2.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all">
        🛑 Ограничение цен
      </button>
    </div>

    <!-- Active Restrictions -->
    <div class="glass-card rounded-2xl p-3 space-y-2">
      <div class="text-xs font-bold text-rose-400">Действующие ценовые ограничения (${data.restrictions.length})</div>
      ${data.restrictions.length === 0 ? '<div class="text-[11px] text-slate-500">Нет активных ограничений цен.</div>' : ''}
      <div class="space-y-1.5">
        ${data.restrictions.map(r => `
          <div class="rounded-xl border border-rose-500/30 bg-rose-950/20 p-2 text-[11px] flex justify-between items-center">
            <div>
              <div class="font-bold text-white">${r.item_id ? r.item_id : 'Все товары'} ${r.company_id ? `(Комп. #${r.company_id})` : '(Весь рынок)'}</div>
              <div class="text-[10px] text-rose-300">Диапазон: [${r.min_price ?? '—'}, ${r.max_price ?? '—'}] ₽ · ${r.reason}</div>
            </div>
            <button class="remove-restr-btn px-2 py-1 rounded bg-rose-800 hover:bg-rose-700 text-white text-[10px] font-bold" data-id="${r.id}">Снять</button>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Active Orders list -->
    <div class="glass-card rounded-2xl p-3 space-y-2">
      <div class="text-xs font-bold text-slate-300">Активные ордера на бирже (${data.orders.length})</div>
      ${data.orders.length === 0 ? '<div class="text-[11px] text-slate-500">Биржевой стакан пуст.</div>' : ''}
      <div class="space-y-1 max-h-48 overflow-y-auto">
        ${data.orders.map(o => `
          <div class="rounded-lg border border-slate-700/60 bg-slate-900/50 p-2 text-[10px] flex justify-between items-center font-mono">
            <div>
              <span class="${o.order_type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'} font-bold">${o.order_type}</span>
              <span class="text-slate-200">#${o.company_id} · ${o.item_id}</span>
            </div>
            <div class="text-right">
              <div class="font-bold text-white">${o.price} ₽</div>
              <div class="text-slate-500">${o.remaining_qty} шт.</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  // Bind remove restriction
  el.querySelectorAll('.remove-restr-btn').forEach(b => {
    b.addEventListener('click', async () => {
      try {
        if (!confirm('Снять это ценовое ограничение?')) return;
        await NatAPI.removeCreatorRestriction(Number(b.dataset.id));
        showToast('Ограничение успешно снято', 'success');
        await loadMarketTab(el, showToast);
      } catch (e) {
        showToast(e.message, 'error');
      }
    });
  });

  // Modal actions
  const warnBtn = el.querySelector('#open-warn-btn');
  if (warnBtn) {
    warnBtn.addEventListener('click', async () => {
      const compId = prompt('Введите ID компании:');
      if (!compId) return;
      const reason = prompt('Причина официального предупреждения:');
      if (!reason) return;
      try {
        await NatAPI.sendCreatorWarning(Number(compId), reason);
        showToast(`Предупреждение выдано компании #${compId}`, 'success');
        await loadMarketTab(el, showToast);
      } catch (e) {
        showToast(e.message, 'error');
      }
    });
  }

  const restrBtn = el.querySelector('#open-restr-btn');
  if (restrBtn) {
    restrBtn.addEventListener('click', async () => {
      const item = prompt('Товар (оставьте пустым для всех):', '') || null;
      const minP = prompt('Минимальная цена (₽):', '');
      const maxP = prompt('Максимальная цена (₽):', '');
      const reason = prompt('Официальная причина ограничения цен:');
      if (!reason) return;

      try {
        await NatAPI.setCreatorRestriction({
          item_id: item ? item.trim() : null,
          min_price: minP ? parseFloat(minP) : null,
          max_price: maxP ? parseFloat(maxP) : null,
          reason: reason.trim()
        });
        showToast('Ценовое ограничение установлено на сервере', 'success');
        await loadMarketTab(el, showToast);
      } catch (e) {
        showToast(e.message, 'error');
      }
    });
  }
}

async function loadBondsTab(el, showToast) {
  const data = await NatAPI.getCreatorBonds();
  el.innerHTML = `
    <div class="glass-card rounded-2xl p-4 space-y-3">
      <div class="text-xs font-bold text-amber-400 uppercase">Выпуск государственных облигаций</div>
      <div class="space-y-2 text-xs">
        <input id="bond-title" placeholder="Название (напр. ОФЗ-НАТ-1)" class="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white" />
        <div class="grid grid-cols-2 gap-2">
          <input id="bond-vol" type="number" placeholder="Объём (шт.)" class="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white" />
          <input id="bond-face" type="number" placeholder="Номинал (₽)" class="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white" />
        </div>
        <div class="grid grid-cols-2 gap-2">
          <input id="bond-rate" type="number" placeholder="Купон (%)" class="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white" />
          <input id="bond-days" type="number" placeholder="Срок (дней)" class="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white" />
        </div>
        <input id="bond-purpose" placeholder="Цель привлечения средств" class="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white" />
        <button id="issue-bond-btn" class="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 font-bold text-white text-xs transition-all shadow-md">
          Выпустить облигации
        </button>
      </div>
    </div>

    <div class="glass-card rounded-2xl p-3 space-y-2">
      <div class="text-xs font-bold text-slate-300">Размещённые облигации (${data.bonds.length})</div>
      <div class="space-y-1.5">
        ${data.bonds.map(b => `
          <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-2.5 text-[11px] font-mono">
            <div class="flex justify-between font-bold text-white">
              <span>${b.title}</span>
              <span class="text-amber-400">${b.coupon_rate}% годовых</span>
            </div>
            <div class="text-[10px] text-slate-400 mt-1">
              Остаток: ${b.remaining_volume} / ${b.total_volume} шт. по ${b.face_value} ₽ · Срок: ${b.maturity_days} дн.
            </div>
            <div class="text-[9px] text-slate-500 italic mt-0.5">${b.purpose}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  const issueBtn = el.querySelector('#issue-bond-btn');
  if (issueBtn) {
    issueBtn.addEventListener('click', async () => {
      const title = el.querySelector('#bond-title').value.trim();
      const vol = parseInt(el.querySelector('#bond-vol').value, 10);
      const face = parseFloat(el.querySelector('#bond-face').value);
      const rate = parseFloat(el.querySelector('#bond-rate').value);
      const days = parseInt(el.querySelector('#bond-days').value, 10);
      const purpose = el.querySelector('#bond-purpose').value.trim();

      if (!title || !vol || !face || !days || !purpose) {
        return showToast('Заполните все поля эмиссии', 'error');
      }

      if (!confirm(`Выпустить ${vol} облигаций «${title}» по ${face} cash? Выпуск сам по себе не создаёт деньги.`)) return;
      try {
        await NatAPI.issueCreatorBonds({
          title, volume: vol, face_value: face, coupon_rate: rate || 0, maturity_days: days, purpose
        });
        showToast(`Облигации «${title}» выпущены. Казна пополняется только при фактической покупке.`, 'success');
        await loadBondsTab(el, showToast);
      } catch (e) {
        showToast(e.message, 'error');
      }
    });
  }
}

async function loadTournamentsTab(el, showToast) {
  el.innerHTML = `
    <div class="glass-card rounded-2xl p-4 space-y-3">
      <div class="text-xs font-bold text-amber-400 uppercase">Управление Турнирами 11 «Б»</div>
      <p class="text-[11px] text-slate-400">
        Обычный цикл: старт раз в 72 часа, длительность 18 часов. Здесь можно запустить отдельный турнир с собственным призовым фондом PVC.
      </p>
      <div class="grid grid-cols-3 gap-2">
        <label class="text-[10px] text-amber-300">🥇 1 место
          <input id="tourn-reward-first" type="number" inputmode="numeric" min="0" max="10000" step="1" value="150" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-sm text-white outline-none focus:border-amber-400">
        </label>
        <label class="text-[10px] text-slate-300">🥈 2 место
          <input id="tourn-reward-second" type="number" inputmode="numeric" min="0" max="10000" step="1" value="100" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-sm text-white outline-none focus:border-amber-400">
        </label>
        <label class="text-[10px] text-orange-300">🥉 3 место
          <input id="tourn-reward-third" type="number" inputmode="numeric" min="0" max="10000" step="1" value="70" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-sm text-white outline-none focus:border-amber-400">
        </label>
      </div>
      <p class="text-[10px] text-slate-500">Награды выдаются в Pivocoins (PVC). Допустимо от 0 до 10 000 PVC за место.</p>
      <button id="launch-tourn-btn" class="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs transition-all shadow-lg shadow-amber-500/20">
        ⚔️ Запустить кастомный турнир на 18 часов
      </button>
    </div>
  `;

  const btn = el.querySelector('#launch-tourn-btn');
  if (btn) {
    btn.addEventListener('click', async () => {
      const rewards = [
        Number(el.querySelector('#tourn-reward-first')?.value),
        Number(el.querySelector('#tourn-reward-second')?.value),
        Number(el.querySelector('#tourn-reward-third')?.value),
      ];
      if (!rewards.every(value => Number.isInteger(value) && value >= 0 && value <= 10000)) {
        showToast('Укажите целые призы от 0 до 10 000 PVC.', 'error');
        return;
      }
      if (!confirm(`Запустить 18-часовой турнир с наградами ${rewards[0]} / ${rewards[1]} / ${rewards[2]} PVC?`)) return;
      try {
        const res = await NatAPI.launchCreatorTournament({
          reward_first_pvc: rewards[0],
          reward_second_pvc: rewards[1],
          reward_third_pvc: rewards[2],
        });
        showToast(`Турнир №${res.number} запущен на 18 часов.`, 'success');
        btn.disabled = true;
        btn.textContent = 'Турнир запущен';
      } catch (e) {
        showToast(e.message, 'error');
      }
    });
  }
}

async function loadAuditTab(el, showToast) {
  const data = await NatAPI.getCreatorAuditLog();
  el.innerHTML = `
    <div class="glass-card rounded-2xl p-3 space-y-2">
      <div class="text-xs font-bold text-slate-300">Журнал действий Администратора (${data.logs.length})</div>
      <div class="space-y-1.5 max-h-96 overflow-y-auto">
        ${data.logs.map(l => `
          <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-2 text-[10px]">
            <div class="flex justify-between font-mono">
              <span class="text-amber-400 font-bold">${l.action}</span>
              <span class="text-slate-500">${new Date(l.created_at).toLocaleTimeString('ru-RU')}</span>
            </div>
            <div class="text-slate-300 mt-0.5">${l.details || ''}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
