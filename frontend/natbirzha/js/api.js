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
  const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null;
  if (tg && tg.initData && tg.initData.length > 0) {
    return { 'X-Telegram-Init-Data': tg.initData };
  }
  // Local browser / dev test fallback
  let tgUserId = null;
  if (typeof window !== 'undefined' && window.location) {
    const params = new URLSearchParams(window.location.search);
    tgUserId = params.get('tg_user_id');
  }
  if (tgUserId) {
    try { sessionStorage.setItem('nat_dev_user_id', tgUserId); } catch (_) {}
  } else {
    try { tgUserId = sessionStorage.getItem('nat_dev_user_id'); } catch (_) {}
  }
  if (!tgUserId && tg?.initDataUnsafe?.user?.id) {
    tgUserId = String(tg.initDataUnsafe.user.id);
  }
  if (!tgUserId && typeof window !== 'undefined' && window.location && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    tgUserId = '12345';
  }
  if (tgUserId) {
    const userPayload = JSON.stringify({
      id: parseInt(tgUserId, 10),
      first_name: tg?.initDataUnsafe?.user?.first_name || 'DevUser'
    });
    return { 'X-Telegram-Init-Data': `user=${encodeURIComponent(userPayload)}` };
  }
  return {};
}

function parseErrorMessage(data, status) {
  if (!data) return `Ошибка сервера (${status})`;
  if (typeof data === 'string') return data;

  const detail = data.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map(e => e.msg || e.message || (typeof e === 'object' ? JSON.stringify(e) : String(e))).join('; ');
  }
  if (detail && typeof detail === 'object') {
    if (typeof detail.error === 'string') return detail.error;
    if (typeof detail.message === 'string') return detail.message;
    if (typeof detail.reason === 'string') {
      const reasonMap = {
        'insufficient_inventory': 'Недостаточно ресурсов на складе',
        'insufficient_cash': 'Недостаточно cash на балансе',
        'maximum_territory_limit': 'Достигнут максимум территории',
        'factory_not_found': 'Предприятие не найдено',
        'company_not_found': 'Компания не найдена',
      };
      return reasonMap[detail.reason] || detail.reason;
    }
    return JSON.stringify(detail);
  }
  if (typeof data.message === 'string') return data.message;
  if (typeof data.error === 'string') return data.error;
  if (data.reason && typeof data.reason === 'string') return data.reason;
  return `Ошибка сервера (${status})`;
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
    const errorMsg = parseErrorMessage(data, response.status);
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
  expandTerritory: () => request('/api/natbirzha/company/territory/expand', { method: 'POST' }),
  createCompany: (payload) => request('/api/natbirzha/company/create', { method: 'POST', body: JSON.stringify(payload) }),
  respecCompany: (specialization) => request('/api/natbirzha/company/respec', { method: 'POST', body: JSON.stringify({ new_specialization: specialization }) }),

  // Production
  getProductionStatus: () => request('/api/natbirzha/production/factories'),
  getRecipes: () => request('/api/natbirzha/production/recipes'),
  getInventory: () => request('/api/natbirzha/production/inventory'),
  buildFactory: (factory_type) => request('/api/natbirzha/production/factory/build', {
    method: 'POST',
    body: JSON.stringify({ building_type: factory_type, factory_type })
  }),
  triggerProduction: (factory_id, recipe_id) => request('/api/natbirzha/production/factory/produce', {
    method: 'POST',
    body: JSON.stringify({ factory_id: parseInt(factory_id, 10), recipe_id })
  }),

  // Market
  getOrderbook: (item_id) => request(`/api/natbirzha/market/orderbook?item_id=${item_id}`),
  getNpcRates: () => request('/api/natbirzha/market/npc/rates'),
  placeOrder: (payload) => request('/api/natbirzha/market/order/place', { method: 'POST', body: JSON.stringify(payload) }),
  cancelOrder: (order_id) => request('/api/natbirzha/market/order/cancel', { method: 'POST', body: JSON.stringify({ order_id: parseInt(order_id, 10) }) }),
  npcTrade: (payload) => request('/api/natbirzha/market/npc/trade', { method: 'POST', body: JSON.stringify(payload) }),

  // Stocks & IPO
  getStocksList: () => request('/api/natbirzha/stocks/market'),
  issueIPO: (payload = {}) => request('/api/natbirzha/stocks/ipo/apply', { method: 'POST', body: JSON.stringify(payload) }),
  buyShares: (stock_id, shares_count) => request('/api/natbirzha/stocks/buy', { method: 'POST', body: JSON.stringify({ stock_id: parseInt(stock_id, 10), shares_count: parseInt(shares_count, 10) }) }),
  getPortfolio: () => request('/api/natbirzha/stocks/portfolio'),

  // Military, Alliances & Tournaments
  getMilitaryStatus: () => request('/api/natbirzha/military/status'),
  recruitUnits: (unit_type, count) => request('/api/natbirzha/military/recruit', { method: 'POST', body: JSON.stringify({ unit_type, count: parseInt(count, 10) }) }),
  getCurrentTournament: () => request('/api/natbirzha/military/tournaments/current'),
  joinAlliance: (alliance_id) => request('/api/natbirzha/military/alliance/join', { method: 'POST', body: JSON.stringify({ alliance_id: parseInt(alliance_id, 10) }) }),

  // Bankruptcy
  getBankruptcyStatus: () => request('/api/natbirzha/bankruptcy/status'),
  submitRestructuring: () => request('/api/natbirzha/bankruptcy/file', { method: 'POST' }),
};
