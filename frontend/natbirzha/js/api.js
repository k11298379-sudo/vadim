/**
 * Natbirzha API Client
 * Strictly handles Telegram initData authentication and Idempotency-Key generation.
 */

function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getAuthHeader() {
  const tg = window.Telegram?.WebApp;
  if (tg && tg.initData && tg.initData.length > 0) {
    return { 'X-Telegram-Init-Data': tg.initData };
  }
  // Local browser test fallback
  const params = new URLSearchParams(window.location.search);
  let tgUserId = params.get('tg_user_id');
  if (tgUserId) {
    try { sessionStorage.setItem('nat_dev_user_id', tgUserId); } catch (_) {}
  } else {
    try { tgUserId = sessionStorage.getItem('nat_dev_user_id'); } catch (_) {}
  }
  if (!tgUserId && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    tgUserId = '12345';
  }
  if (tgUserId) {
    const userPayload = JSON.stringify({ id: parseInt(tgUserId, 10), first_name: 'DevUser' });
    return { 'X-Telegram-Init-Data': `user=${encodeURIComponent(userPayload)}` };
  }
  return {};
}

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('/') ? endpoint : `/api/natbirzha/${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  // Add Idempotency-Key for state-modifying requests
  if (options.method && options.method.toUpperCase() === 'POST') {
    if (!headers['Idempotency-Key']) {
      headers['Idempotency-Key'] = generateUUID();
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let errorMsg = `Ошибка сервера (${response.status})`;
    if (typeof data.detail === 'string') {
      errorMsg = data.detail;
    } else if (Array.isArray(data.detail) && data.detail.length > 0) {
      errorMsg = data.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
    } else if (data.detail && typeof data.detail === 'object') {
      errorMsg = data.detail.error || data.detail.message || JSON.stringify(data.detail);
    } else if (data.message && typeof data.message === 'string') {
      errorMsg = data.message;
    } else if (data.error && typeof data.error === 'string') {
      errorMsg = data.error;
    }
    const error = new Error(errorMsg);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

export const NatAPI = {
  // Auth & Company
  login: () => request('/api/natbirzha/auth/login', { method: 'POST' }),
  getMyCompany: () => request('/api/natbirzha/company/me'),
  createCompany: (payload) => request('/api/natbirzha/company/create', { method: 'POST', body: JSON.stringify(payload) }),
  respecCompany: (specialization) => request('/api/natbirzha/company/respec', { method: 'POST', body: JSON.stringify({ specialization }) }),

  // Production
  getProductionStatus: () => request('/api/natbirzha/production/status'),
  buildFactory: (factory_type) => request('/api/natbirzha/production/factory/build', {
    method: 'POST',
    body: JSON.stringify({ building_type: factory_type, factory_type })
  }),
  triggerProduction: (factory_id, recipe_id) => request('/api/natbirzha/production/factory/produce', {
    method: 'POST',
    body: JSON.stringify({ factory_id, recipe_id })
  }),

  // Market
  getOrderbook: (item_id) => request(`/api/natbirzha/market/orderbook?item_id=${item_id}`),
  placeOrder: (payload) => request('/api/natbirzha/market/order/place', { method: 'POST', body: JSON.stringify(payload) }),
  cancelOrder: (order_id) => request('/api/natbirzha/market/order/cancel', { method: 'POST', body: JSON.stringify({ order_id }) }),
  npcTrade: (payload) => request('/api/natbirzha/market/npc/trade', { method: 'POST', body: JSON.stringify(payload) }),

  // Stocks & IPO
  getStocksList: () => request('/api/natbirzha/stocks/list'),
  issueIPO: (payload) => request('/api/natbirzha/stocks/ipo', { method: 'POST', body: JSON.stringify(payload) }),
  placeStockOrder: (payload) => request('/api/natbirzha/stocks/order/place', { method: 'POST', body: JSON.stringify(payload) }),
  claimDividends: (holding_id) => request('/api/natbirzha/stocks/dividends/claim', { method: 'POST', body: JSON.stringify({ holding_id }) }),

  // Military & Tournaments
  getMilitaryStatus: () => request('/api/natbirzha/military/status'),
  recruitUnits: (unit_type, count) => request('/api/natbirzha/military/recruit', { method: 'POST', body: JSON.stringify({ unit_type, count }) }),
  getCurrentTournament: () => request('/api/natbirzha/military/tournaments/current'),

  // Bankruptcy
  getBankruptcyStatus: () => request('/api/natbirzha/bankruptcy/status'),
  submitRestructuring: (terms) => request('/api/natbirzha/bankruptcy/plan/submit', { method: 'POST', body: JSON.stringify({ terms }) }),
};
