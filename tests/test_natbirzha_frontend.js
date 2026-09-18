const fs = require('fs');
const path = require('path');
const assert = require('assert');

console.log('=== [Natbirzha Test 1/5] Testing index.html markup & theme sync ===');
const natHtml = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/index.html'), 'utf-8');
assert(natHtml.includes('id="screen-container"'), 'index.html must have screen-container');
assert(natHtml.includes('id="bottom-nav"'), 'index.html must have bottom-nav');
assert(natHtml.includes('id="toast-container"'), 'index.html must have toast-container');
assert(natHtml.includes('id="header-stats"'), 'index.html must have header-stats');
assert(natHtml.includes('id="header-cash"'), 'index.html must have header-cash');
assert(natHtml.includes('id="header-ticker"'), 'index.html must have header-ticker');
assert(natHtml.includes('/static/natbirzha/css/natbirzha.css'), 'index.html must import natbirzha.css');
assert(natHtml.includes('/static/natbirzha/js/app.js'), 'index.html must import app.js');
assert(natHtml.includes('syncTgTheme'), 'index.html must define syncTgTheme');
assert(natHtml.includes("window.Telegram?.WebApp?.onEvent?.('themeChanged'"), 'index.html must safely listen to themeChanged');
console.log('index.html structure and scripts verified!');

console.log('=== [Natbirzha Test 2/5] Testing state.js reactivity & non-destructive updates ===');
const stateScript = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/state.js'), 'utf-8');
const cleanedStateScript = stateScript.replace(/export\s+const\s+store\s+=/, 'const store =');
const stateFn = new Function(cleanedStateScript + '\nreturn { NatStateStore, store };');
const { store } = stateFn();

assert(!store.hasCompany(), 'Initial state must not have company');
store.setUser({ id: 10, full_name: 'Трейдер' });
assert(store.user && store.user.id === 10, 'User state must be set');

store.setCompany({
  company_id: 101,
  name: 'Северсталь 11 Б',
  ticker: 'ST11',
  cash: 50000,
  audited_nav: 50000,
  inventory: { steel: 10, coal: 20 },
  factories: [{ id: 1, building_type: 'smelter', level: 1 }]
});
assert(store.hasCompany(), 'hasCompany must return true after setCompany');
assert(store.company.id === 101, 'company_id must be normalized to id');
assert(store.nav === 50000, 'nav must be populated from audited_nav');
assert(store.inventory.steel === 10, 'inventory must be set');
assert(store.factories.length === 1, 'factories must be set');

store.updateCompany({ factories: [{ id: 1, building_type: 'smelter', level: 2 }], inventory: undefined });
assert(store.inventory.steel === 10, 'inventory must NOT be wiped when undefined is passed to updateCompany');
assert(store.factories[0].level === 2, 'factories must be updated');
assert(store.company.name === 'Северсталь 11 Б', 'other company fields must be preserved');

store.setTab('production');
assert(store.currentTab === 'production', 'setTab must update currentTab');
console.log('state.js reactivity and safe updates verified!');

console.log('=== [Natbirzha Test 3/5] Testing api.js request handling & error resilience ===');
const apiScript = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/api.js'), 'utf-8');
const cleanedApiScript = apiScript.replace(/export\s+const\s+NatAPI\s+=/, 'const NatAPI =');
const apiFn = new Function('window', 'crypto', 'sessionStorage', cleanedApiScript + '\nreturn { NatAPI, parseErrorMessage, getAuthHeader, generateUUID };');

const mockBrowserWindow = {
  location: { search: '?tg_user_id=777', hostname: 'localhost' },
  Telegram: { WebApp: { initData: 'auth_signature_xyz' } }
};
const mockSessionStorage = {
  _store: {},
  getItem: function(k) { return this._store[k]; },
  setItem: function(k, v) { return this._store[k] = v; }
};
const mockCrypto = { randomUUID: () => '11111111-2222-3333-4444-555555555555' };

const { NatAPI, parseErrorMessage, getAuthHeader, generateUUID } = apiFn(mockBrowserWindow, mockCrypto, mockSessionStorage);

assert(generateUUID() === '11111111-2222-3333-4444-555555555555', 'generateUUID must return UUID');
assert(getAuthHeader()['X-Telegram-Init-Data'] === 'auth_signature_xyz', 'Telegram WebApp initData must be prioritized');

const mockDevWindow = {
  location: { search: '?tg_user_id=888', hostname: '127.0.0.1' },
  Telegram: {}
};
const { getAuthHeader: getDevAuthHeader } = apiFn(mockDevWindow, mockCrypto, mockSessionStorage);
const devHeader = getDevAuthHeader()['X-Telegram-Init-Data'];
assert(devHeader && devHeader.includes('888'), 'Dev fallback must encode tg_user_id in user payload');

const err1 = parseErrorMessage({ detail: 'Баланс исчерпан' }, 400);
assert(err1 === 'Баланс исчерпан', 'string detail must be extracted');
assert(!err1.includes('[object Object]'), 'must never contain [object Object]');

const err2 = parseErrorMessage({ detail: [{ msg: 'Field required', loc: ['name'] }] }, 422);
assert(err2 === 'Field required', 'array validation errors must be formatted cleanly');

const err3 = parseErrorMessage({ detail: { reason: 'insufficient_inventory', needed: 10, available: 2 } }, 400);
assert(err3.includes('Недостаточно ресурсов на складе') || err3.includes('insufficient_inventory'), 'detail reason must be translated or formatted');
assert(!err3.includes('[object Object]'), 'detail object must never format to [object Object]');

const err4 = parseErrorMessage({}, 500);
assert(err4.includes('Ошибка сервера (500)'), 'empty object must produce readable server error');

const requiredMethods = [
  'login', 'getMyCompany', 'expandTerritory', 'createCompany', 'respecCompany',
  'getProductionStatus', 'getRecipes', 'getInventory', 'buildFactory', 'triggerProduction',
  'getOrderbook', 'getNpcRates', 'placeOrder', 'cancelOrder', 'npcTrade',
  'getStocksList', 'issueIPO', 'buyShares', 'getPortfolio',
  'getMilitaryStatus', 'recruitUnits', 'getCurrentTournament', 'joinAlliance',
  'getBankruptcyStatus', 'submitRestructuring'
];
requiredMethods.forEach(m => {
  assert(typeof NatAPI[m] === 'function', `NatAPI.${m} must be defined`);
});
console.log('api.js methods, auth headers and error handling resilience verified!');

console.log('=== [Natbirzha Test 4/5] Testing screen modules syntax & exports ===');
const screens = ['onboarding.js', 'overview.js', 'production.js', 'upgrades.js', 'market.js', 'stocks.js', 'military.js'];
screens.forEach(s => {
  const code = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/', s), 'utf-8');
  const renderFnName = 'render' + s[0].toUpperCase() + s.slice(1).replace('.js', '');
  assert(code.includes(`export function ${renderFnName}`) || code.includes(`export async function ${renderFnName}`),
    `${s} must export ${renderFnName}`);
});

const prodCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/production.js'), 'utf-8');
assert(prodCode.includes('f.building_type || f.factory_type'), 'production.js must handle both building_type and factory_type');
assert(prodCode.includes('food_processing'), 'production.js must contain canonical food_processing recipe id');
assert(prodCode.includes('mine_rare_lithium'), 'production.js must contain canonical mine_rare_lithium recipe id');

const marketCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/market.js'), 'utf-8');
assert(marketCode.includes('finally'), 'market.js place order must have finally block to re-enable button');

const milCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/military.js'), 'utf-8');
assert(milCode.includes('joinAlliance'), 'military.js must support joining alliances');

const appCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/app.js'), 'utf-8');
assert(appCode.includes("msgText === '[object Object]'"), 'app.js showToast must guard against [object Object]');
assert(appCode.includes('window.NatApp'), 'app.js must expose window.NatApp');
assert(appCode.includes('navigateTo'), 'app.js must export navigateTo');
console.log('All screen modules and app.js integration verified!');

console.log('=== [Natbirzha Test 5/5] Testing games.js Natbirzha banner exposure ===');
const gamesCode = fs.readFileSync(path.join(__dirname, '../frontend/js/games.js'), 'utf-8');
assert(gamesCode.includes('НАТБИРЖА'), 'games.js must contain Natbirzha banner definition');
assert(gamesCode.includes('${isTesterUser ?'), 'games.js must condition Natbirzha banner on isTesterUser');
assert(gamesCode.includes('/app/natbirzha'), 'Natbirzha banner must link to /app/natbirzha');
console.log('Natbirzha banner in games.js verified!');

console.log('\n🌟 ALL NATBIRZHA FRONTEND TESTS PASSED WITH 100% SUCCESS! 🌟');
