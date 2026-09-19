import { NatAPI, setNavigationAbortSignal } from './api.js';
import { store } from './state.js';
import { renderOnboarding } from './screens/onboarding.js';
import { renderOverview } from './screens/overview.js';
import { renderProduction } from './screens/production.js';
import { renderUpgrades } from './screens/upgrades.js';
import { renderMarket } from './screens/market.js';
import { renderStocks } from './screens/stocks.js';
import { renderMilitary } from './screens/military.js';
import { renderCreator } from './screens/creator.js';
import { renderLeaderboard } from './screens/leaderboard.js';
import { renderHelp } from './screens/help.js';

// Telegram Haptic Feedback Helper
export function triggerHaptic(type = 'light') {
  try {
    const haptic = window.Telegram?.WebApp?.HapticFeedback;
    if (!haptic) return;
    if (type === 'success' || type === 'error' || type === 'warning') {
      haptic.notificationOccurred?.(type);
    } else if (type === 'selection') {
      haptic.selectionChanged?.();
    } else {
      haptic.impactOccurred?.(type);
    }
  } catch (_) {}
}

// Toast Notification Manager (100% resilient against [object Object])
export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const bgColors = {
    info: 'bg-blue-600 text-white',
    success: 'bg-emerald-600 text-white',
    error: 'bg-rose-600 text-white',
  };

  let msgText = '';
  if (typeof message === 'string') {
    msgText = message;
  } else if (message instanceof Error) {
    msgText = message.message;
    if ((!msgText || msgText === '[object Object]') && message.data) {
      msgText = typeof message.data.detail === 'string' ? message.data.detail : JSON.stringify(message.data.detail || message.data);
    }
  } else if (typeof message === 'object' && message !== null) {
    const raw = message.message || message.error || message.detail || message.reason || message;
    if (typeof raw === 'string') {
      msgText = raw;
    } else if (typeof raw === 'object' && raw !== null) {
      msgText = raw.msg || raw.message || raw.error || JSON.stringify(raw);
    } else {
      msgText = String(raw);
    }
  } else {
    msgText = String(message || '');
  }

  if (!msgText || msgText === '[object Object]') {
    msgText = type === 'error' ? 'Произошла непредвиденная ошибка' : 'Действие выполнено';
  }

  triggerHaptic(type === 'error' ? 'error' : type === 'success' ? 'success' : 'light');

  const toast = document.createElement('div');
  toast.className = `toast-msg px-4 py-2.5 rounded-xl shadow-xl text-xs font-bold flex items-center gap-2 ${bgColors[type] || bgColors.info}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '⚠' : 'ℹ'}</span><span>${msgText}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.25s ease-out';
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}

let activeRenderPromise = null;
let renderRequested = false;
let navigationId = 0;
let navigationAbortController = null;

function beginNavigationScope() {
  navigationId += 1;
  navigationAbortController?.abort();
  navigationAbortController = new AbortController();
  setNavigationAbortSignal(navigationAbortController.signal);
  return navigationId;
}

function isAbortError(error) {
  return error?.name === 'AbortError' || error?.code === 20;
}

// Render one stable state. The public coordinator below serializes async screens
// so a slow response cannot overwrite the tab selected by a later tap.
async function renderScreenOnce() {
  const renderNavigationId = navigationId;
  const renderTab = store.currentTab;
  const container = document.getElementById('screen-container');
  if (!container) return;
  const renderContainer = document.createElement('div');

  // If no company exists yet, always route to Onboarding
  if (!store.hasCompany()) {
    document.getElementById('bottom-nav')?.classList.add('hidden');
    document.getElementById('header-stats')?.classList.add('hidden');
    renderOnboarding(renderContainer, showToast);
    if (renderNavigationId !== navigationId) {
      renderRequested = true;
      return;
    }
    container.replaceChildren(renderContainer);
    return;
  }

  // Show navigation and stats
  document.getElementById('bottom-nav')?.classList.remove('hidden');
  document.getElementById('header-stats')?.classList.remove('hidden');

  // Update header stats
  const company = store.company;
  const cashEl = document.getElementById('header-cash');
  const tickerEl = document.getElementById('header-ticker');
  const tickerText = company?.ticker || (company?.name ? company.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 5) : 'CORP');
  if (cashEl && company) cashEl.innerText = `${Math.round(company.cash || 0).toLocaleString('ru-RU')} cash`;
  if (tickerEl && company) tickerEl.innerText = `[${tickerText}]`;

  // Update active tab styles
  document.querySelectorAll('.nav-tab').forEach(btn => {
    const tab = btn.getAttribute('data-tab');
    if (tab === store.currentTab) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Render selected screen
  container.innerHTML = '<div class="p-8 text-center text-xs text-slate-400">Загрузка...</div>';
  switch (renderTab) {
    case 'overview':
      renderOverview(renderContainer, showToast);
      break;
    case 'production':
      await renderProduction(renderContainer, showToast);
      break;
    case 'upgrades':
      await renderUpgrades(renderContainer, showToast);
      break;
    case 'market':
      await renderMarket(renderContainer, showToast);
      break;
    case 'stocks':
      await renderStocks(renderContainer, showToast);
      break;
    case 'military':
      await renderMilitary(renderContainer, showToast);
      break;
    case 'leaderboard':
      await renderLeaderboard(renderContainer, showToast);
      break;
    case 'help':
      renderHelp(renderContainer, showToast);
      break;
    case 'creator':
      await renderCreator(renderContainer, showToast);
      break;
    default:
      renderOverview(renderContainer, showToast);
  }
  // The screen renders off-DOM. An outdated request can therefore never
  // replace the currently selected tab after its fetches complete.
  if (renderNavigationId !== navigationId) {
    renderRequested = true;
    return;
  }
  container.replaceChildren(renderContainer);
}

// Coalesce rapid navigation into the latest requested tab. Screen renderers keep
// their existing local state and event handlers, while only one owns the DOM at a time.
export async function renderCurrentScreen() {
  renderRequested = true;
  if (activeRenderPromise) return activeRenderPromise;

  const running = (async () => {
    while (renderRequested) {
      renderRequested = false;
      try {
        await renderScreenOnce();
      } catch (error) {
        if (!isAbortError(error)) throw error;
      }
    }
  })();
  activeRenderPromise = running;

  try {
    await running;
  } finally {
    if (activeRenderPromise === running) activeRenderPromise = null;
  }

  // Defensive edge case: a request arriving during promise cleanup still wins.
  if (renderRequested) return renderCurrentScreen();
}

// Programmatic tab navigation
export async function navigateTo(tab) {
  if (!tab) return;
  triggerHaptic('selection');
  beginNavigationScope();
  store.setTab(tab);
  await renderCurrentScreen();
}

// Setup bottom navigation listeners
function setupNavigation() {
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      if (tab && tab !== store.currentTab) {
        navigateTo(tab);
      }
    });
  });

  const creatorBtn = document.getElementById('creator-nav-btn');
  if (creatorBtn) {
    creatorBtn.addEventListener('click', () => {
      navigateTo('creator');
    });
  }
}

// App Initialization
export async function initApp() {
  const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null;
  if (tg) {
    try { tg.ready?.(); } catch (_) {}
    try { tg.expand?.(); } catch (_) {}
  }

  setupNavigation();

  if (!tg?.initData) {
    const container = document.getElementById('screen-container');
    if (container) {
      container.innerHTML = `
        <div class="max-w-md mx-auto p-6 pt-12 text-center">
          <div class="glass-card rounded-2xl p-6 space-y-3">
            <div class="text-4xl">🔐</div>
            <h2 class="text-lg font-black">Откройте НАТБИРЖУ из Telegram</h2>
            <p class="text-xs text-slate-500">Для входа требуется подписанный Telegram Mini App initData. Вход по URL-параметру или сохранённому ID отключён.</p>
          </div>
        </div>`;
    }
    return;
  }

  // Subscribe to state updates
  store.subscribe(() => {
    const company = store.company;
    const cashEl = document.getElementById('header-cash');
    const tickerEl = document.getElementById('header-ticker');
    const tickerText = company?.ticker || (company?.name ? company.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 5) : 'CORP');
    if (cashEl && company) cashEl.innerText = `${Math.round(company.cash || 0).toLocaleString('ru-RU')} cash`;
    if (tickerEl && company) tickerEl.innerText = `[${tickerText}]`;
  });

  try {
    // 1. Authenticate user
    const authData = await NatAPI.login();
    store.setUser(authData.user);

    // Reveal Creator button for admin / state creator
    const user = authData.user;
    if (user?.is_creator === true) {
      const creatorBtn = document.getElementById('creator-nav-btn');
      if (creatorBtn) creatorBtn.classList.remove('hidden');
    }

    // 2. Check company existence from auth response first
    if (authData.has_company) {
      try {
        const company = await NatAPI.getMyCompany();
        if (company) {
          store.setCompany(company);
        }
      } catch (e) {
        // If getMyCompany fails but auth says has_company=true,
        // create minimal company from auth data
        store.setCompany({
          id: authData.company_id,
          company_id: authData.company_id,
          name: authData.company_name,
          specialization: authData.specialization,
          cash: 0,
          ticker: authData.company_name ? authData.company_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 5) : 'CORP'
        });
      }
    }
    // If has_company is false, store.company stays null -> onboarding
  } catch (err) {
    console.error('App init error:', err);
    showToast(err.message || 'Ошибка подключения к серверу', 'error');
    const container = document.getElementById('screen-container');
    if (container) {
      container.innerHTML = `<div class="max-w-md mx-auto p-6 text-center"><div class="glass-card rounded-2xl p-6"><div class="text-3xl mb-3">🔐</div><h2 class="font-black mb-2">Откройте НАТБИРЖУ из Telegram</h2><p class="text-xs text-slate-500">Для входа нужен подписанный Telegram Mini App initData. ID из URL или браузерного хранилища не используется.</p></div></div>`;
    }
    return;
  }

  beginNavigationScope();
  await renderCurrentScreen();
}

if (typeof window !== 'undefined') {
  window.NatApp = {
    navigateTo,
    renderCurrentScreen,
    showToast,
    triggerHaptic,
    store,
    NatAPI,
    initApp
  };
  window.addEventListener('DOMContentLoaded', initApp);
}
