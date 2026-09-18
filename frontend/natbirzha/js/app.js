import { NatAPI } from './api.js';
import { store } from './state.js';
import { renderOnboarding } from './screens/onboarding.js';
import { renderOverview } from './screens/overview.js';
import { renderProduction } from './screens/production.js';
import { renderMarket } from './screens/market.js';
import { renderStocks } from './screens/stocks.js';
import { renderMilitary } from './screens/military.js';

// Toast Notification Manager
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
  } else if (typeof message === 'object' && message !== null) {
    msgText = message.message || message.error || message.detail || JSON.stringify(message);
  } else {
    msgText = String(message || '');
  }

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

// Render active screen
async function renderCurrentScreen() {
  const container = document.getElementById('screen-container');
  if (!container) return;

  // If no company exists yet, always route to Onboarding
  if (!store.hasCompany()) {
    document.getElementById('bottom-nav')?.classList.add('hidden');
    document.getElementById('header-stats')?.classList.add('hidden');
    renderOnboarding(container, showToast);
    return;
  }

  // Show navigation and stats
  document.getElementById('bottom-nav')?.classList.remove('hidden');
  document.getElementById('header-stats')?.classList.remove('hidden');

  // Update header stats
  const company = store.company;
  const cashEl = document.getElementById('header-cash');
  const tickerEl = document.getElementById('header-ticker');
  if (cashEl && company) cashEl.innerText = `${Math.round(company.cash).toLocaleString()} cash`;
  if (tickerEl && company) tickerEl.innerText = `[${company.ticker}]`;

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
  switch (store.currentTab) {
    case 'overview':
      renderOverview(container, showToast);
      break;
    case 'production':
      await renderProduction(container, showToast);
      break;
    case 'market':
      await renderMarket(container, showToast);
      break;
    case 'stocks':
      await renderStocks(container, showToast);
      break;
    case 'military':
      await renderMilitary(container, showToast);
      break;
    default:
      renderOverview(container, showToast);
  }
}

// Setup bottom navigation listeners
function setupNavigation() {
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      if (tab && tab !== store.currentTab) {
        store.setTab(tab);
        renderCurrentScreen();
      }
    });
  });
}

// App Initialization
async function initApp() {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    try {
      tg.expand();
    } catch (_) {}
  }

  setupNavigation();

  // Subscribe to state updates
  store.subscribe(() => {
    const company = store.company;
    const cashEl = document.getElementById('header-cash');
    const tickerEl = document.getElementById('header-ticker');
    if (cashEl && company) cashEl.innerText = `${Math.round(company.cash).toLocaleString()} cash`;
    if (tickerEl && company) tickerEl.innerText = `[${company.ticker}]`;
  });

  try {
    // 1. Authenticate user
    const authData = await NatAPI.login();
    store.setUser(authData.user);

    // 2. Load existing company
    try {
      const company = await NatAPI.getMyCompany();
      if (company && company.id) {
        store.setCompany(company);
      }
    } catch (e) {
      // 404 means no company registered yet -> proceed to onboarding
      console.log('No company found, directing to onboarding.');
    }
  } catch (err) {
    console.error('App init error:', err);
    showToast(err.message || 'Ошибка подключения к серверу', 'error');
  }

  await renderCurrentScreen();
}

window.addEventListener('DOMContentLoaded', initApp);
