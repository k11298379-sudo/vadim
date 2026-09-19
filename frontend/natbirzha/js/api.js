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

const TELEGRAM_INIT_DATA_STORAGE_KEY = 'natbirzha_telegram_init_data';

function getTelegramInitData() {
  const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null;
  if (tg?.initData && typeof tg.initData === 'string') return tg.initData;
  try {
    if (typeof sessionStorage !== 'undefined') {
      return sessionStorage.getItem(TELEGRAM_INIT_DATA_STORAGE_KEY) || '';
    }
  } catch (_) {}
  return '';
}

function getAuthHeader() {
  const initData = getTelegramInitData();
  if (!initData || typeof initData !== 'string' || initData.length === 0) {
    return {};
  }
  return { 'X-Telegram-Init-Data': initData };
}

// App navigation owns this signal. A request started for a screen that the
// player has already left must not keep the old screen alive.
let navigationAbortSignal = null;
export function setNavigationAbortSignal(signal) {
  navigationAbortSignal = signal || null;
}

// Immutable catalog-like responses are reused briefly across tabs. Dynamic
// balances, inventories and order books intentionally never enter this cache.
const responseCache = new Map();

function cachedGet(endpoint, ttlMs) {
  const now = Date.now();
  const cached = responseCache.get(endpoint);
  if (cached && cached.expiresAt > now) return Promise.resolve(cached.data);

  return request(endpoint).then((data) => {
    responseCache.set(endpoint, { data, expiresAt: Date.now() + ttlMs });
    return data;
  });
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
    if (typeof detail.reason === 'string') {
      const reasonMap = {
        'insufficient_inventory': 'Недостаточно ресурсов на складе',
        'insufficient_cash': 'Недостаточно cash на балансе',
        'maximum_territory_limit': 'Достигнут максимум территории',
        'factory_not_found': 'Предприятие не найдено',
        'company_not_found': 'Компания не найдена',
        'npc_volume_limit': 'Лимит ликвидности Госрезерва на сегодня исчерпан',
        'inventory_overflow': 'Склад переполнен',
        'cooldown': 'Эта цель недавно проиграла вам. Повторная атака будет доступна через 2 часа',
        'tournament_not_active': 'PvP доступно только во время активного турнира',
        'tournament_not_found': 'Турнир не найден',
        'attacker_not_participant': 'Ваша компания не участвует в этом турнире',
        'target_not_participant': 'Выбранная компания не участвует в турнире',
        'self_attack': 'Нельзя атаковать собственную компанию',
        'empty_army': 'Сначала сформируйте армию',
        'target_empty_army': 'У цели не осталось армии',
        'insufficient_ground_force': 'Для захвата нужна выжившая наземная армия',
        'already_conquered': 'Эта PvE-корпорация уже захвачена',
        'prerequisite': 'Сначала захватите предыдущую PvE-корпорацию',
        'company_level': 'Уровень компании слишком низкий для этой цели',
      };
      return reasonMap[detail.reason] || detail.reason;
    }
    if (typeof detail.message === 'string') return detail.message;
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
  if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
    if (!headers['Idempotency-Key']) {
      headers['Idempotency-Key'] = generateUUID();
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    signal: options.signal || navigationAbortSignal || undefined,
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

  // Production & Buildings
  getProductionStatus: () => request('/api/natbirzha/production/factories'),
  getRecipes: () => cachedGet('/api/natbirzha/production/recipes', 5 * 60 * 1000),
  getInventory: () => request('/api/natbirzha/production/inventory'),
  getBuildingsCatalog: () => cachedGet('/api/natbirzha/buildings/catalog', 5 * 60 * 1000),
  getBuildingDetails: (factory_id) => request(`/api/natbirzha/buildings/${factory_id}`),
  getFactoryUpgrades: (factory_id) => request(`/api/natbirzha/factories/${factory_id}/upgrades`),
  buildEnterprise: (building_type) => request('/api/natbirzha/buildings/build', {
    method: 'POST',
    body: JSON.stringify({ building_type })
  }),
  buildFactory: (factory_type) => request('/api/natbirzha/buildings/build', {
    method: 'POST',
    body: JSON.stringify({ building_type: factory_type, factory_type })
  }),
  triggerProduction: (factory_id, recipe_id) => request('/api/natbirzha/production/factory/produce', {
    method: 'POST',
    body: JSON.stringify({ factory_id: parseInt(factory_id, 10), recipe_id })
  }),

  upgradeFactory: (factory_id, upgrade_type) => request('/api/natbirzha/factories/' + factory_id + '/upgrade', { method: 'POST', body: JSON.stringify({ upgrade_type }) }),

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
  sellShares: (stock_id, shares_count) => request('/api/natbirzha/stocks/sell', { method: 'POST', body: JSON.stringify({ stock_id: parseInt(stock_id, 10), shares_count: parseInt(shares_count, 10) }) }),
  getPortfolio: () => request('/api/natbirzha/stocks/portfolio'),

  // Military, Alliances & Tournaments
  getMilitaryStatus: () => request('/api/natbirzha/military/status'),
  recruitUnits: (unit_type, count) => request('/api/natbirzha/military/recruit', { method: 'POST', body: JSON.stringify({ unit_type, count: parseInt(count, 10) }) }),
  getCurrentTournament: () => request('/api/natbirzha/military/tournaments/current'),
  getPveTargets: () => request('/api/natbirzha/military/pve/targets'),
  scoutPveTarget: (target_code) => request(`/api/natbirzha/military/pve/targets/${encodeURIComponent(target_code)}/scout`, { method: 'POST' }),
  attackPveTarget: (target_code) => request(`/api/natbirzha/military/pve/targets/${encodeURIComponent(target_code)}/attack`, { method: 'POST' }),
  getBattleHistory: () => request('/api/natbirzha/military/battles'),
  getTournamentHistory: () => request('/api/natbirzha/military/tournaments/history'),
  getTournamentTargets: (tournament_id) => request(`/api/natbirzha/military/tournaments/${parseInt(tournament_id, 10)}/targets`),
  attackTournamentTarget: (tournament_id, company_id) => request(`/api/natbirzha/military/tournaments/${parseInt(tournament_id, 10)}/targets/${parseInt(company_id, 10)}/attack`, { method: 'POST' }),
  joinAlliance: (alliance_id) => request('/api/natbirzha/military/alliance/join', { method: 'POST', body: JSON.stringify({ alliance_id: parseInt(alliance_id, 10) }) }),

  // Official-reference instruments (server prices only)
  getReferenceInstruments: () => cachedGet('/api/natbirzha/instruments', 30 * 1000),
  tradeReferenceInstrument: (instrument_code, side, quantity) => request('/api/natbirzha/instruments/trade', {
    method: 'POST',
    body: JSON.stringify({ instrument_code, side, quantity: parseFloat(quantity) })
  }),

  // Bankruptcy
  getBankruptcyStatus: () => request('/api/natbirzha/bankruptcy/status'),
  submitRestructuring: () => request('/api/natbirzha/bankruptcy/file', { method: 'POST' }),
  resetCompany: () => request('/api/natbirzha/company/reset', { method: 'POST' }),

  // State bonds (player-facing purchase; treasury receives only transferred player cash)
  getStateBonds: () => request('/api/natbirzha/bonds'),
  buyStateBonds: (bond_id, quantity) => request(`/api/natbirzha/bonds/${bond_id}/buy`, {
    method: 'POST',
    body: JSON.stringify({ quantity: parseInt(quantity, 10) })
  }),
  createBondListing: (bond_id, quantity, unit_price) => request('/api/natbirzha/bonds/listings', {
    method: 'POST',
    body: JSON.stringify({ bond_id: parseInt(bond_id, 10), quantity: parseInt(quantity, 10), unit_price: parseFloat(unit_price) })
  }),
  buyBondListing: (listing_id) => request(`/api/natbirzha/bonds/listings/${parseInt(listing_id, 10)}/buy`, { method: 'POST' }),
  cancelBondListing: (listing_id) => request(`/api/natbirzha/bonds/listings/${parseInt(listing_id, 10)}`, { method: 'DELETE' }),

  // Pivocoins and time-limited premium branch
  getPremiumWallet: () => request('/api/natbirzha/premium/wallet'),
  getPremiumLedger: () => request('/api/natbirzha/premium/ledger'),
  getPremiumLicenseCatalog: () => cachedGet('/api/natbirzha/premium/licenses/catalog', 5 * 60 * 1000),
  getPremiumLicenses: () => request('/api/natbirzha/premium/licenses'),
  purchasePremiumLicense: (license_code) => request(`/api/natbirzha/premium/licenses/${encodeURIComponent(license_code)}/purchase`, { method: 'POST' }),
  getPremiumUpgradeCatalog: () => cachedGet('/api/natbirzha/premium/upgrades/catalog', 5 * 60 * 1000),
  getPremiumUpgrades: () => request('/api/natbirzha/premium/upgrades'),
  purchasePremiumUpgrade: (upgrade_code) => request(`/api/natbirzha/premium/upgrades/${encodeURIComponent(upgrade_code)}/purchase`, { method: 'POST' }),

  // Public company rankings (all values are calculated on the server)
  getLeaderboard: (category = 'assets', page = 1) => request(`/api/natbirzha/leaderboard?category=${encodeURIComponent(category)}&page=${parseInt(page, 10)}`),

  // Creator / State Administration
  getCreatorOverview: () => request('/api/natbirzha/creator/overview'),
  getCreatorMarket: () => request('/api/natbirzha/creator/market'),
  sendCreatorWarning: (company_id, reason) => request('/api/natbirzha/creator/market/warnings', { method: 'POST', body: JSON.stringify({ company_id: parseInt(company_id, 10), reason }) }),
  setCreatorRestriction: (payload) => request('/api/natbirzha/creator/market/restrictions', { method: 'POST', body: JSON.stringify(payload) }),
  removeCreatorRestriction: (restriction_id) => request(`/api/natbirzha/creator/market/restrictions/${restriction_id}`, { method: 'DELETE' }),
  issueCreatorBonds: (payload) => request('/api/natbirzha/creator/bonds/issue', { method: 'POST', body: JSON.stringify(payload) }),
  getCreatorBonds: () => request('/api/natbirzha/creator/bonds'),
  launchCreatorTournament: (payload = {}) => request('/api/natbirzha/creator/tournaments/launch', { method: 'POST', body: JSON.stringify(payload) }),
  getCreatorAuditLog: () => request('/api/natbirzha/creator/audit-log'),
  getCreatorPremiumLedger: (company_id = null) => request(`/api/natbirzha/creator/premium/ledger${company_id ? `?company_id=${parseInt(company_id, 10)}` : ''}`),
  getCreatorPlayers: ({ search = '', sort = 'last_activity_at', page = 1 } = {}) => request(`/api/natbirzha/creator/players?search=${encodeURIComponent(search)}&sort=${encodeURIComponent(sort)}&page=${parseInt(page, 10)}`),
};
