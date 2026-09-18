import { NatAPI } from '../api.js';
import { store } from '../state.js';

export async function renderStocks(container, showToast) {
  let stocksList = [];
  try {
    const res = await NatAPI.getStocksList();
    stocksList = res.stocks || [];
  } catch (err) {
    console.error('Failed to load stocks:', err);
  }

  const myCompany = store.company || {};
  const isPublic = myCompany.is_public;

  container.innerHTML = `
    <div class="space-y-4 max-w-md mx-auto p-4 pb-24">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-black text-slate-900 dark:text-white">Фондовая Биржа</h2>
          <p class="text-xs text-slate-500">Акции, первичное размещение (IPO) и дивиденды</p>
        </div>
      </div>

      <!-- IPO Banner / Status -->
      <div class="glass-card rounded-2xl p-4 shadow-sm border-l-4 ${isPublic ? 'border-l-emerald-500' : 'border-l-blue-500'} space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xl">${isPublic ? '🏛️' : '🚀'}</span>
            <div>
              <div class="text-xs font-bold text-slate-900 dark:text-white">
                ${isPublic ? 'Ваша корпорация торгуется на бирже' : 'Выход на IPO'}
              </div>
              <div class="text-[11px] text-slate-400">
                ${isPublic ? '60% основатель, 40% free-float в открытом обращении' : 'Привлеките капитал инвесторов под залог доли компании'}
              </div>
            </div>
          </div>
          ${!isPublic ? `
            <button id="open-ipo-btn" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-xs shadow-md active:scale-95 transition-all">
              Выйти на IPO
            </button>
          ` : `
            <span class="text-xs font-bold font-mono text-emerald-500">АКТИВНО</span>
          `}
        </div>

        ${isPublic ? `
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 dark:border-slate-800 text-xs">
            <div>
              <span class="text-slate-400 text-[11px]">Дивидендный пул:</span>
              <div class="font-mono font-bold text-emerald-500">10% от чистой прибыли</div>
            </div>
            <div>
              <span class="text-slate-400 text-[11px]">Режим выплат:</span>
              <div class="font-mono font-bold text-slate-300">Ежедневно 00:01</div>
            </div>
          </div>
        ` : ''}
      </div>

      <!-- Stock Market List -->
      <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Котировки публичных корпораций</h3>
          <span class="text-xs font-mono text-slate-400">${stocksList.length} эмитентов</span>
        </div>

        <div class="space-y-2">
          ${stocksList.length === 0 ? `
            <div class="text-center py-6 text-slate-400 text-xs">
              На бирже пока нет размещённых акций. Будьте первыми!
            </div>
          ` : stocksList.map(s => `
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <div>
                <div class="flex items-center gap-1.5">
                  <span class="font-mono font-black text-xs text-blue-600 dark:text-blue-400">[${s.ticker}]</span>
                  <span class="font-bold text-xs text-slate-900 dark:text-white">${s.company_name}</span>
                </div>
                <div class="text-[10px] text-slate-400 mt-0.5">Free-float: ${s.free_float_shares?.toLocaleString()} шт.</div>
              </div>
              <div class="text-right">
                <div class="font-mono font-black text-xs text-slate-900 dark:text-white">${s.current_price?.toFixed(2)} cash</div>
                <button
                  class="buy-shares-btn mt-1 px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] active:scale-95 transition-all"
                  data-stock-id="${s.id}"
                  data-ticker="${s.ticker}"
                  data-price="${s.current_price}"
                >
                  Купить
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>

    <!-- IPO Modal -->
    <div id="ipo-modal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm hidden items-center justify-center p-4">
      <div class="glass-card rounded-2xl max-w-sm w-full p-5 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between">
          <h3 class="font-black text-slate-900 dark:text-white text-base">Первичное размещение (IPO)</h3>
          <button id="close-ipo-modal-btn" class="text-slate-400 hover:text-slate-600 text-lg">✕</button>
        </div>
        <p class="text-xs text-slate-400">
          При выходе на биржу выпускается 1,000,000 акций. 60% остаётся у вас, 40% выставляется на свободный рынок.
        </p>
        <div class="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs space-y-1 font-mono">
          <div class="flex justify-between">
            <span class="text-slate-500">Оценка NAV:</span>
            <span class="font-bold text-slate-900 dark:text-white">${store.nav || 10000} cash</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Цена размещения:</span>
            <span class="font-bold text-emerald-500">${((store.nav || 10000) / 1000000).toFixed(4)} cash / акция</span>
          </div>
        </div>
        <button
          id="confirm-ipo-btn"
          class="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs active:scale-98 transition-all"
        >
          🚀 Подтвердить выпуск акций
        </button>
      </div>
    </div>
  `;

  // IPO Modal handlers
  const ipoModal = container.querySelector('#ipo-modal');
  container.querySelector('#open-ipo-btn')?.addEventListener('click', () => {
    ipoModal.classList.remove('hidden');
    ipoModal.classList.add('flex');
  });
  container.querySelector('#close-ipo-modal-btn')?.addEventListener('click', () => {
    ipoModal.classList.add('hidden');
    ipoModal.classList.remove('flex');
  });

  container.querySelector('#confirm-ipo-btn')?.addEventListener('click', async () => {
    const btn = container.querySelector('#confirm-ipo-btn');
    try {
      btn.disabled = true;
      btn.innerText = 'Размещение...';
      await NatAPI.issueIPO({});
      ipoModal.classList.add('hidden');
      showToast('IPO успешно проведено! Акции вышли на биржу.', 'success');
      const refreshed = await NatAPI.getMyCompany();
      store.setCompany(refreshed);
      renderStocks(container, showToast);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerText = '🚀 Подтвердить выпуск акций';
    }
  });

  // Buy shares handler
  container.querySelectorAll('.buy-shares-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const stockId = btn.getAttribute('data-stock-id');
      const ticker = btn.getAttribute('data-ticker');
      const price = parseFloat(btn.getAttribute('data-price'));
      const countStr = prompt(`Сколько акций [${ticker}] купить по цене ${price.toFixed(4)} cash?`, '1000');
      const count = parseInt(countStr, 10);
      if (!count || count <= 0) return;

      try {
        await NatAPI.placeStockOrder({ stock_id: stockId, side: 'buy', amount: count, price });
        showToast(`Ордер на покупку акций [${ticker}] размещен!`, 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderStocks(container, showToast);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  });
}
