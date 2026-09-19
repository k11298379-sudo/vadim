import { NatAPI } from '../api.js';
import { store } from '../state.js';

const MARKET_ITEMS = [
  { id: 'steel', name: 'Сталь', unit: 'т', base: 90.0, buy: 72.0, sell: 112.5 },
  { id: 'iron_ore', name: 'Железная руда', unit: 'т', base: 35.0, buy: 28.0, sell: 43.75 },
  { id: 'coal', name: 'Каменный уголь', unit: 'т', base: 30.0, buy: 24.0, sell: 37.5 },
  { id: 'energy', name: 'Электроэнергия', unit: 'МВт·ч', base: 10.0, buy: 8.0, sell: 12.5 },
  { id: 'oil_crude', name: 'Сырая нефть', unit: 'барр.', base: 50.0, buy: 40.0, sell: 62.5 },
  { id: 'fuel_diesel', name: 'Дизельное топливо', unit: 'л', base: 1.2, buy: 0.96, sell: 1.5 },
  { id: 'grain', name: 'Зерно', unit: 'т', base: 20.0, buy: 16.0, sell: 25.0 },
  { id: 'fertilizer', name: 'Удобрения', unit: 'т', base: 50.0, buy: 40.0, sell: 62.5 },
  { id: 'wood_raw', name: 'Лес-кругляк', unit: 'м³', base: 25.0, buy: 20.0, sell: 31.25 },
  { id: 'aluminum', name: 'Алюминий', unit: 'т', base: 110.0, buy: 88.0, sell: 137.5 },
];

const INSTRUMENT_NAMES = { USD: 'Доллар США', EUR: 'Евро', GOLD: 'Золото', SILVER: 'Серебро' };
const INSTRUMENT_ICONS = { USD: '💵', EUR: '💶', GOLD: '🥇', SILVER: '🥈' };
const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, ch => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[ch]));

export async function renderMarket(container, showToast) {
  let selectedItemId = 'steel';
  let orderbookData = null;
  let orderbookRequestId = 0;
  let instrumentsData = { instruments: [], portfolio: [] };
  let bondsData = { bonds: [], holdings: [], listings: [] };

  async function loadOrderbook() {
    const requestId = ++orderbookRequestId;
    try {
      const data = await NatAPI.getOrderbook(selectedItemId);
      if (requestId !== orderbookRequestId) return false;
      orderbookData = data;
      return true;
    } catch (err) {
      if (requestId !== orderbookRequestId) return false;
      console.error('Failed to load orderbook:', err);
      return false;
    }
  }

  async function loadFinancialMarkets() {
    const [instruments, bonds] = await Promise.allSettled([
      NatAPI.getReferenceInstruments(),
      NatAPI.getStateBonds(),
    ]);
    if (instruments.status === 'fulfilled') instrumentsData = instruments.value || instrumentsData;
    if (bonds.status === 'fulfilled') bondsData = bonds.value || bondsData;
  }

  const [ratesData] = await Promise.all([
    NatAPI.getNpcRates().catch(() => null),
    loadOrderbook(),
    loadFinancialMarkets(),
  ]);

  if (ratesData && Array.isArray(ratesData.rates)) {
    for (const r of ratesData.rates) {
      const item = MARKET_ITEMS.find(m => m.id === r.item_id);
      if (item) {
        item.base = r.base_price;
        item.buy = r.npc_buy_price;
        item.sell = r.npc_sell_price;
        if (r.unit) item.unit = r.unit;
      }
    }
  }

  function renderView() {
    const selectorScrollLeft = container.querySelector('.market-resource-tabs')?.scrollLeft || 0;
    const itemInfo = MARKET_ITEMS.find(i => i.id === selectedItemId) || MARKET_ITEMS[0];
    const bids = orderbookData?.bids || [];
    const asks = orderbookData?.asks || [];
    const userOrders = orderbookData?.user_orders || [];
    const userInvQty = store.inventory[selectedItemId] || 0;
    const positions = new Map((instrumentsData.portfolio || []).map(row => [row.instrument_code, row]));
    const ownCompanyId = Number(store.company?.id || store.company?.company_id || 0);

    container.innerHTML = `
      <div class="space-y-4 max-w-md mx-auto p-4 pb-24">
        <!-- Resource Selector Bar -->
        <div class="market-resource-tabs flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
          ${MARKET_ITEMS.map(item => `
            <button
              class="market-item-tab px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                item.id === selectedItemId
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
              }"
              data-item-id="${item.id}"
            >
              ${item.name}
            </button>
          `).join('')}
        </div>

        <!-- Official currency and metal instruments: same Market screen -->
        <details class="glass-card rounded-2xl p-4 shadow-sm space-y-3" open>
          <summary class="cursor-pointer list-none flex items-center justify-between">
            <div><h3 class="text-xs font-bold uppercase tracking-wider text-slate-500">Валюты и металлы</h3><p class="text-[9px] text-slate-400">Официальный курс ЦБ · цена задаётся сервером</p></div><span class="text-lg">🏦</span>
          </summary>
          <div class="grid grid-cols-2 gap-2 pt-3">
            ${(instrumentsData.instruments || []).map(instrument => {
              const position = positions.get(instrument.code) || {};
              return `<div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-2">
                <div class="flex justify-between"><span class="text-lg">${INSTRUMENT_ICONS[instrument.code] || '💱'}</span><span class="text-[9px] font-bold ${instrument.available ? 'text-emerald-500' : 'text-rose-500'}">${instrument.available ? 'Курс актуален' : 'Торги приостановлены'}</span></div>
                <div><div class="text-xs font-black">${INSTRUMENT_NAMES[instrument.code] || instrument.code}</div><div class="text-[9px] text-slate-400">Позиция: ${Number(position.quantity || 0).toLocaleString('ru-RU')}</div></div>
                ${instrument.reference_rub ? `<div class="text-[10px] font-mono"><span class="text-emerald-600">${Number(instrument.sell_rub).toFixed(2)} ₽</span> / <span class="text-rose-600">${Number(instrument.buy_rub).toFixed(2)} ₽</span></div>` : '<div class="text-[10px] text-slate-400">Курс ещё не загружен</div>'}
                <div class="grid grid-cols-2 gap-1"><button class="instrument-trade-btn py-1.5 rounded-lg bg-blue-600 text-white text-[10px] font-bold disabled:opacity-50" data-code="${instrument.code}" data-side="buy" ${instrument.available ? '' : 'disabled'}>Купить</button><button class="instrument-trade-btn py-1.5 rounded-lg bg-emerald-600 text-white text-[10px] font-bold disabled:opacity-50" data-code="${instrument.code}" data-side="sell" ${instrument.available && Number(position.quantity || 0) > 0 ? '' : 'disabled'}>Продать</button></div>
                ${instrument.quoted_at ? `<div class="text-[8px] text-slate-400">Котировка: ${new Date(instrument.quoted_at).toLocaleDateString('ru-RU')}</div>` : ''}
              </div>`;
            }).join('') || '<div class="col-span-2 text-xs text-slate-400 text-center py-2">Официальные курсы пока не получены</div>'}
          </div>
        </details>

        <!-- State bonds and protected secondary listings -->
        <details class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
          <summary class="cursor-pointer list-none flex items-center justify-between"><div><h3 class="text-xs font-bold uppercase tracking-wider text-slate-500">Гособлигации</h3><p class="text-[9px] text-slate-400">Купоны, погашение и вторичный рынок</p></div><span class="text-lg">📜</span></summary>
          <div class="space-y-3 pt-3">
            ${(bondsData.bonds || []).map(bond => `<div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"><div class="flex justify-between gap-2"><div><div class="text-xs font-black">${esc(bond.title)}</div><div class="text-[9px] text-slate-400">${bond.coupon_rate}% · купон каждые ${bond.coupon_interval_days || 7} дн. · ${esc(bond.status || '')}</div></div><div class="text-right"><div class="text-xs font-mono font-bold">${Number(bond.face_value).toFixed(2)} cash</div><div class="text-[9px] text-slate-400">остаток ${bond.remaining_volume}</div></div></div>${bond.is_active ? `<button class="buy-primary-bond-btn mt-2 w-full py-1.5 rounded-lg bg-blue-600 text-white text-[10px] font-bold disabled:opacity-50" data-bond-id="${bond.id}" data-title="${esc(bond.title)}">Купить у государства</button>` : ''}</div>`).join('') || '<div class="text-xs text-slate-400">Нет выпусков</div>'}
            ${(bondsData.holdings || []).filter(row => row.available_quantity > 0).length ? `<div><div class="text-[10px] font-bold uppercase text-slate-400 mb-1">Ваш портфель</div>${bondsData.holdings.filter(row => row.available_quantity > 0).map(row => `<div class="flex items-center justify-between p-2 rounded-lg bg-amber-50 dark:bg-amber-950/20 text-xs"><span>${esc(row.title)} · ${row.quantity} шт.</span><button class="create-bond-listing-btn text-blue-600 font-bold" data-bond-id="${row.bond_id}" data-available="${row.available_quantity}">Продать</button></div>`).join('')}</div>` : ''}
            <div><div class="text-[10px] font-bold uppercase text-slate-400 mb-1">Вторичные предложения</div>${(bondsData.listings || []).filter(row => row.status === 'OPEN').map(row => `<div class="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-xs"><div><div class="font-bold">Выпуск #${row.bond_id} · ${row.quantity} шт.</div><div class="text-[9px] text-slate-400">${Number(row.unit_price).toFixed(2)} cash/шт. · всего ${Number(row.total_cost).toFixed(2)}</div></div>${Number(row.seller_company_id) === ownCompanyId ? `<button class="cancel-bond-listing-btn text-rose-500 font-bold" data-listing-id="${row.listing_id}">Снять</button>` : `<button class="buy-bond-listing-btn px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold disabled:opacity-50" data-listing-id="${row.listing_id}">Купить</button>`}</div>`).join('') || '<div class="text-[10px] text-slate-400">Открытых предложений нет</div>'}</div>
          </div>
        </details>

        <!-- NPC Reserve Liquidity Banner -->
        <div class="glass-card rounded-2xl p-4 shadow-sm space-y-2 border-l-4 border-l-amber-500">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
              Резервный фонд NPC (Гарантированный коридор)
            </span>
            <span class="text-[10px] font-mono text-slate-400">База: ${itemInfo.base} cash</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
              <div class="text-[10px] font-semibold text-emerald-700 dark:text-emerald-300">Скупка NPC (Пол -20%)</div>
              <div class="font-mono font-black text-sm text-emerald-600 dark:text-emerald-400">${itemInfo.buy.toFixed(2)} cash</div>
              <button class="npc-sell-btn mt-1 w-full py-1 rounded bg-emerald-600 text-white font-bold text-[11px] active:scale-95 transition-all">
                Сдать NPC
              </button>
            </div>
            <div class="p-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800">
              <div class="text-[10px] font-semibold text-rose-700 dark:text-rose-300">Продажа NPC (Потолок +25%)</div>
              <div class="font-mono font-black text-sm text-rose-600 dark:text-rose-400">${itemInfo.sell.toFixed(2)} cash</div>
              <button class="npc-buy-btn mt-1 w-full py-1 rounded bg-rose-600 text-white font-bold text-[11px] active:scale-95 transition-all">
                Купить у NPC
              </button>
            </div>
          </div>
          <div class="text-[10px] text-slate-400">
            На вашем складе: <span class="font-mono font-bold text-slate-700 dark:text-slate-200">${userInvQty} ${itemInfo.unit}</span>
          </div>
        </div>

        <!-- Orderbook (Стакан биржи) -->
        <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Биржевой стакан цен</h3>
            <span class="text-[11px] text-slate-500 font-bold">${itemInfo.name}</span>
          </div>

          <div class="grid grid-cols-2 gap-3 text-xs">
            <!-- Asks (Продажа) -->
            <div class="space-y-1">
              <div class="text-[10px] font-bold text-rose-500 uppercase">Продажа (Asks)</div>
              ${asks.length === 0 ? '<div class="text-slate-400 text-[10px]">Нет заявок</div>' : asks.slice(0, 5).map(a => `
                <div class="flex justify-between font-mono p-1 rounded depth-ask text-[11px]">
                  <span class="text-rose-600 font-bold">${a.price.toFixed(2)}</span>
                  <span class="text-slate-500">${a.remaining_qty} ${itemInfo.unit}</span>
                </div>
              `).join('')}
            </div>

            <!-- Bids (Покупка) -->
            <div class="space-y-1">
              <div class="text-[10px] font-bold text-emerald-500 uppercase">Покупка (Bids)</div>
              ${bids.length === 0 ? '<div class="text-slate-400 text-[10px]">Нет заявок</div>' : bids.slice(0, 5).map(b => `
                <div class="flex justify-between font-mono p-1 rounded depth-bid text-[11px]">
                  <span class="text-emerald-600 font-bold">${b.price.toFixed(2)}</span>
                  <span class="text-slate-500">${b.remaining_qty} ${itemInfo.unit}</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Place Limit Order Form -->
        <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Выставить биржевой ордер</h3>
          <form id="place-order-form" class="space-y-3">
            <div class="grid grid-cols-2 gap-2">
              <label class="flex items-center justify-center p-2 rounded-xl border border-slate-300 dark:border-slate-700 cursor-pointer has-[:checked]:bg-emerald-600 has-[:checked]:text-white has-[:checked]:border-emerald-600 transition-all text-xs font-bold">
                <input type="radio" name="order_side" value="buy" checked class="hidden" />
                🟢 Покупка
              </label>
              <label class="flex items-center justify-center p-2 rounded-xl border border-slate-300 dark:border-slate-700 cursor-pointer has-[:checked]:bg-rose-600 has-[:checked]:text-white has-[:checked]:border-rose-600 transition-all text-xs font-bold">
                <input type="radio" name="order_side" value="sell" class="hidden" />
                🔴 Продажа
              </label>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[10px] font-bold text-slate-500 mb-1 uppercase">Количество (${itemInfo.unit})</label>
                <input type="number" id="order-qty" min="1" step="1" value="10" required class="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs font-mono text-slate-900 dark:text-white" />
              </div>
              <div>
                <label class="block text-[10px] font-bold text-slate-500 mb-1 uppercase">Цена (cash)</label>
                <input type="number" id="order-price" min="0.1" step="0.1" value="${itemInfo.base}" required class="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs font-mono text-slate-900 dark:text-white" />
              </div>
            </div>

            <button type="submit" id="submit-order-btn" class="w-full py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs shadow-md shadow-blue-500/25 hover:bg-blue-700 active:scale-98 transition-all">
              Разместить ордер в стакан
            </button>
          </form>
        </div>

        <!-- Open User Orders -->
        ${userOrders.length > 0 ? `
          <div class="glass-card rounded-2xl p-4 shadow-sm space-y-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Ваши активные ордера</h3>
            <div class="space-y-1.5">
              ${userOrders.map(o => `
                <div class="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between text-xs font-mono">
                  <div class="flex items-center gap-2">
                    <span class="font-bold ${o.order_type === 'buy' ? 'text-emerald-500' : 'text-rose-500'}">
                      ${o.order_type.toUpperCase()}
                    </span>
                    <span>${o.remaining_quantity} @ ${o.price} cash</span>
                  </div>
                  <button class="cancel-order-btn text-rose-500 hover:text-rose-700 text-[11px] font-bold" data-order-id="${o.id}">
                    Отменить
                  </button>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;

    const resourceTabs = container.querySelector('.market-resource-tabs');
    if (resourceTabs) resourceTabs.scrollLeft = selectorScrollLeft;

    // Tab click listeners
    container.querySelectorAll('.market-item-tab').forEach(btn => {
      btn.addEventListener('click', async () => {
        const nextItemId = btn.getAttribute('data-item-id');
        if (!nextItemId || nextItemId === selectedItemId) return;
        selectedItemId = nextItemId;
        if (await loadOrderbook()) renderView();
      });
    });

    container.querySelectorAll('.instrument-trade-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const quantity = parseFloat(prompt(`Количество ${btn.dataset.code}:`, '1'));
        if (!quantity || quantity <= 0) return;
        btn.disabled = true;
        try {
          await NatAPI.tradeReferenceInstrument(btn.dataset.code, btn.dataset.side, quantity);
          await loadFinancialMarkets();
          const company = await NatAPI.getMyCompany();
          store.setCompany(company);
          showToast('Сделка исполнена по серверному курсу', 'success');
          renderView();
        } catch (err) { showToast(err.message, 'error'); btn.disabled = false; }
      });
    });

    container.querySelectorAll('.buy-primary-bond-btn').forEach(btn => btn.addEventListener('click', async () => {
      const quantity = parseInt(prompt(`Сколько облигаций «${btn.dataset.title}» купить?`, '1'), 10);
      if (!quantity || quantity <= 0) return;
      btn.disabled = true;
      try { await NatAPI.buyStateBonds(btn.dataset.bondId, quantity); await loadFinancialMarkets(); store.setCompany(await NatAPI.getMyCompany()); showToast('Облигации куплены', 'success'); renderView(); }
      catch (err) { showToast(err.message, 'error'); btn.disabled = false; }
    }));

    container.querySelectorAll('.create-bond-listing-btn').forEach(btn => btn.addEventListener('click', async () => {
      const quantity = parseInt(prompt(`Количество для продажи (доступно ${btn.dataset.available}):`, '1'), 10);
      const price = parseFloat(prompt('Цена за одну облигацию:', '1000'));
      if (!quantity || quantity <= 0 || !price || price <= 0) return;
      btn.disabled = true;
      try { await NatAPI.createBondListing(btn.dataset.bondId, quantity, price); await loadFinancialMarkets(); showToast('Облигации выставлены на вторичный рынок', 'success'); renderView(); }
      catch (err) { showToast(err.message, 'error'); btn.disabled = false; }
    }));

    container.querySelectorAll('.buy-bond-listing-btn').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true;
      try { await NatAPI.buyBondListing(btn.dataset.listingId); await loadFinancialMarkets(); store.setCompany(await NatAPI.getMyCompany()); showToast('Листинг куплен', 'success'); renderView(); }
      catch (err) { showToast(err.message, 'error'); btn.disabled = false; }
    }));

    container.querySelectorAll('.cancel-bond-listing-btn').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true;
      try { await NatAPI.cancelBondListing(btn.dataset.listingId); await loadFinancialMarkets(); showToast('Листинг снят', 'info'); renderView(); }
      catch (err) { showToast(err.message, 'error'); btn.disabled = false; }
    }));

    // NPC Trade handlers
    container.querySelector('.npc-sell-btn')?.addEventListener('click', async () => {
      const qtyStr = prompt(`Сколько единиц ${itemInfo.name} сдать NPC по цене ${itemInfo.buy.toFixed(2)} cash?`, '10');
      const qty = parseFloat(qtyStr);
      if (!qty || qty <= 0) return;
      try {
        const res = await NatAPI.npcTrade({ item_id: selectedItemId, operation: 'sell', quantity: qty });
        showToast(res.message || 'Сделка с NPC завершена!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        await loadOrderbook();
        renderView();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    container.querySelector('.npc-buy-btn')?.addEventListener('click', async () => {
      const qtyStr = prompt(`Сколько единиц ${itemInfo.name} купить у NPC по цене ${itemInfo.sell.toFixed(2)} cash?`, '10');
      const qty = parseFloat(qtyStr);
      if (!qty || qty <= 0) return;
      try {
        const res = await NatAPI.npcTrade({ item_id: selectedItemId, operation: 'buy', quantity: qty });
        showToast(res.message || 'Сделка с NPC завершена!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        await loadOrderbook();
        renderView();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Place Limit Order handler
    container.querySelector('#place-order-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const side = container.querySelector('input[name="order_side"]:checked').value;
      const amount = parseFloat(container.querySelector('#order-qty').value);
      const price = parseFloat(container.querySelector('#order-price').value);

      const btn = container.querySelector('#submit-order-btn');
      try {
        if (btn) {
          btn.disabled = true;
          btn.innerText = 'Размещение...';
        }
        await NatAPI.placeOrder({ item_id: selectedItemId, side, amount, price });
        showToast('Ордер успешно выставлен!', 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        await loadOrderbook();
        renderView();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerText = 'Разместить ордер в стакан';
        }
      }
    });

    // Cancel Order handler
    container.querySelectorAll('.cancel-order-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const orderId = btn.getAttribute('data-order-id');
        try {
          await NatAPI.cancelOrder(orderId);
          showToast('Ордер отменён', 'info');
          const refreshed = await NatAPI.getMyCompany();
          store.setCompany(refreshed);
          await loadOrderbook();
          renderView();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });
  }

  renderView();
}
