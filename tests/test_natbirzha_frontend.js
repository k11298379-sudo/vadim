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
const cleanedApiScript = apiScript
  .replace(/export\s+function\s+setNavigationAbortSignal/, 'function setNavigationAbortSignal')
  .replace(/export\s+const\s+NatAPI\s+=/, 'const NatAPI =');
// Keep the lightweight CommonJS harness compatible with named helper exports.
const normalizedApiScript = cleanedApiScript.replace(/export\s*\{[^}]+\};?/g, '');
const apiFn = new Function('window', 'crypto', 'sessionStorage', normalizedApiScript + '\nreturn { NatAPI, parseErrorMessage, getAuthHeader, generateUUID };');

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
assert(!getDevAuthHeader()['X-Telegram-Init-Data'], 'Unsigned dev/query fallback must be disabled');
assert(/^[a-f0-9-]{16,}$/.test(getDevAuthHeader()['X-Natbirzha-Guest-Id']),
  'Browser access must use a generated guest session identity');
mockSessionStorage._store.natbirzha_telegram_init_data = 'carried_signed_init_data&hash=123';
const { getAuthHeader: getCarriedAuthHeader } = apiFn(mockDevWindow, mockCrypto, mockSessionStorage);
assert(getCarriedAuthHeader()['X-Telegram-Init-Data'] === 'carried_signed_init_data&hash=123',
  'Natbirzha must preserve signed initData when navigating from the parent Mini App');
delete mockSessionStorage._store.natbirzha_telegram_init_data;
assert(!apiScript.includes('initDataUnsafe'), 'api.js must not derive authority from initDataUnsafe');
assert(!apiScript.includes('tg_user_id'), 'api.js must not accept tg_user_id query identity');
assert(apiScript.includes('responseCache') && apiScript.includes('cachedGet'), 'Stable catalog requests must use a TTL cache');
assert(!apiScript.includes('renderCurrentScreen?.()'), 'Generic API errors must not force a full screen render');

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
  'getProductionStatus', 'getRecipes', 'getInventory', 'getFactoryUpgrades', 'buildFactory', 'triggerProduction',
  'getOrderbook', 'getNpcRates', 'placeOrder', 'cancelOrder', 'npcTrade',
  'getStocksList', 'issueIPO', 'buyShares', 'getPortfolio',
  'getMilitaryStatus', 'recruitUnits', 'getCurrentTournament', 'joinAlliance',
  'getPveTargets', 'scoutPveTarget', 'attackPveTarget', 'getBattleHistory',
  'getTournamentTargets', 'attackTournamentTarget', 'getTournamentHistory',
  'getReferenceInstruments', 'tradeReferenceInstrument',
  'getStateBonds', 'createBondListing', 'buyBondListing', 'cancelBondListing',
  'getBankruptcyStatus', 'submitRestructuring'
];
requiredMethods.forEach(m => {
  assert(typeof NatAPI[m] === 'function', `NatAPI.${m} must be defined`);
});
console.log('api.js methods, auth headers and error handling resilience verified!');

console.log('=== [Natbirzha Test 4/5] Testing screen modules syntax & exports ===');
const factoryMapPath = path.join(__dirname, '../frontend/natbirzha/js/factory_map.js');
assert(fs.existsSync(factoryMapPath), 'factory_map.js must define the territory projection');
const factoryMapCode = fs.readFileSync(factoryMapPath, 'utf-8');
['BIOMES', 'getFactoryPage', 'getFactorySlot', 'getBiomeForPage', 'buildFactoryPages'].forEach((name) => {
  assert(factoryMapCode.includes(`export ${name === 'BIOMES' ? 'const' : 'function'} ${name}`),
    `factory_map.js must export ${name}`);
});
assert(factoryMapCode.includes("'map_page'") && factoryMapCode.includes("'map_slot'"),
  'factory map must honor explicit map_page coordinates');
assert(factoryMapCode.includes('null'), 'factory map must preserve empty slots as null');
const natCss = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/css/natbirzha.css'), 'utf-8');
['.factory-map', '.factory-slot', '.factory-biome-grass', '.factory-biome-desert', '.factory-biome-snow'].forEach((selector) => {
  assert(natCss.includes(selector), `natbirzha.css must define ${selector}`);
});
assert(natCss.includes('grid-template-columns: repeat(3'), 'factory map must use a responsive three-column grid');

const screens = ['onboarding.js', 'overview.js', 'production.js', 'upgrades.js', 'market.js', 'stocks.js', 'military.js', 'leaderboard.js', 'help.js'];
screens.forEach(s => {
  const code = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/', s), 'utf-8');
  const renderFnName = 'render' + s[0].toUpperCase() + s.slice(1).replace('.js', '');
  assert(code.includes(`export function ${renderFnName}`) || code.includes(`export async function ${renderFnName}`),
    `${s} must export ${renderFnName}`);
});

const prodCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/production.js'), 'utf-8');
assert(prodCode.includes("from '../factory_map.js'"), 'production.js must use the pure factory map projection');
['factory-map', 'factory-slot', 'factory-next-page', 'factory-collect-btn', 'factory-build-btn'].forEach((hook) => {
  assert(prodCode.includes(hook), `production.js must render ${hook}`);
});
assert(prodCode.includes('cycle_ready_at') && prodCode.includes('remaining_seconds'),
  'production.js must use server cycle timing fields');
assert(prodCode.includes('f.building_type || f.factory_type'), 'production.js must handle both building_type and factory_type');
assert(prodCode.includes('r.factory_type === bType'), 'production.js must render server recipes for the exact factory type');
assert(prodCode.includes('f.current_recipe'), 'production.js must honor server cycle state');
assert(prodCode.includes('NatAPI.triggerProduction'), 'factory map must use the unified production mutation endpoint');
assert(prodCode.includes('factory-collect-btn') && prodCode.includes('openCatalogModal'),
  'factory map must wire collect and catalog actions');
assert(prodCode.includes('button.disabled = true') && prodCode.includes('refreshMap'),
  'factory mutations must lock the clicked control and refresh the map state');
const productionCore = prodCode
  .replace(/^import[^;]+;\s*$/gm, '')
  .replace(/export\s+function\s+renderProduction[\s\S]*/, '')
  .split('function nextStep')[0];
const productionCoreFn = new Function(`${productionCore}\nreturn { cycleState };`);
const { cycleState } = productionCoreFn();
const timerNow = Date.now();
const timerState = cycleState({
  cycle_ready_at: new Date(timerNow + 5000).toISOString(),
  remaining_seconds: 1,
  is_running: true,
}, timerNow);
assert(timerState.remaining >= 4,
  'countdown must derive remaining seconds from cycle_ready_at, not a stale initial snapshot');

const marketCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/market.js'), 'utf-8');
assert(marketCode.includes('finally'), 'market.js place order must have finally block to re-enable button');
assert(marketCode.includes('market-resource-tabs'), 'market.js must keep a stable resource selector hook');
assert(marketCode.includes('selectorScrollLeft'), 'market.js must preserve horizontal resource position across refreshes');

// Every canonical production output must be selectable in the NPC market.
// The API is the source of truth; this regression test prevents a hard-coded
// subset from silently hiding outputs such as natural gas and copper.
assert(marketCode.includes('mergeNpcRatesIntoMarketItems'),
  'market.js must merge every server NPC rate into the resource selector');
const marketHelperCode = marketCode
  .replace(/^import[^;]+;\s*$/gm, '')
  .replace(/export\s+function\s+mergeNpcRatesIntoMarketItems/, 'function mergeNpcRatesIntoMarketItems')
  .replace(/export\s+async\s+function\s+renderMarket[\s\S]*/, '')
  .replace(/export\s+function\s+renderMarket[\s\S]*/, '');
const marketHelperFn = new Function(`${marketHelperCode}\nreturn { MARKET_ITEMS, mergeNpcRatesIntoMarketItems };`);
const { MARKET_ITEMS: initialMarketItems, mergeNpcRatesIntoMarketItems } = marketHelperFn();
const mergedMarketItems = mergeNpcRatesIntoMarketItems([
  { item_id: 'gas_natural', name: 'Природный газ', unit: 'тыс. м³', base_price: 45, npc_buy_price: 36, npc_sell_price: 56.25 },
  { item_id: 'copper', name: 'Медь первичная', unit: 'т', base_price: 60, npc_buy_price: 48, npc_sell_price: 75 },
], initialMarketItems);
assert(mergedMarketItems.some(item => item.id === 'gas_natural'), 'natural gas must be visible in the NPC market');
assert(mergedMarketItems.some(item => item.id === 'copper'), 'copper must be visible in the NPC market');

const milCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/military.js'), 'utf-8');
assert(milCode.includes('joinAlliance'), 'military.js must support joining alliances');
assert(milCode.includes('PvE-границы'), 'military.js must expose PvE borders');
assert(milCode.includes('attackPveTarget'), 'military.js must wire PvE attacks');
assert(milCode.includes('attackTournamentTarget'), 'military.js must wire tournament PvP attacks');
assert(milCode.includes('getTournamentHistory'), 'military.js must show tournament history and personal results');
assert(milCode.includes('Участие автоматическое'), 'tournament screen must explain automatic enrolment before an event starts');
assert(milCode.includes('Pivocoins') && milCode.includes('premium'), 'military.js must expose the separate Pivocoins premium branch');
assert(milCode.includes('purchasePremiumLicense') && milCode.includes('purchasePremiumUpgrade'), 'military.js must wire premium licenses and upgrades');
assert(milCode.includes('border_guards') && milCode.includes('aircraft'), 'military.js must render all six unit types');
assert(natHtml.includes('>Война<'), 'bottom navigation must call the military screen War');
assert(natHtml.includes('data-tab="leaderboard"'), 'bottom navigation must expose the Top screen');

const leaderboardCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/leaderboard.js'), 'utf-8');
assert(leaderboardCode.includes('getLeaderboard') && leaderboardCode.includes('military_rating'), 'leaderboard.js must expose all server-ranked categories');

const helpCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/help.js'), 'utf-8');
assert(helpCode.includes('Pivocoins') && helpCode.includes('IPO') && helpCode.includes('Война'), 'help.js must explain core company progression systems');

assert(marketCode.includes('getReferenceInstruments'), 'market.js must load official reference instruments');
assert(marketCode.includes('tradeReferenceInstrument'), 'market.js must wire reference trades');
assert(marketCode.includes('createBondListing'), 'market.js must expose secondary bond listings');
assert(marketCode.includes('market-section-btn') && marketCode.includes('renderStockDetail') && marketCode.includes('renderBondDetail'),
  'market.js must expose the agreed vertical market sections and drill-down cards');
assert((natHtml.match(/data-tab="stocks"/g) || []).length === 0,
  'stocks must be opened from the single Market tab, not a duplicate bottom tab');

const creatorCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/creator.js'), 'utf-8');
assert(creatorCode.includes('tourn-reward-first') && creatorCode.includes('tourn-reward-second') && creatorCode.includes('tourn-reward-third'),
  'creator.js must expose three independent custom tournament reward fields');
assert(creatorCode.includes('reward_first_pvc') && creatorCode.includes('reward_second_pvc') && creatorCode.includes('reward_third_pvc'),
  'creator.js must submit all three custom tournament rewards');
assert(creatorCode.includes('getCreatorPremiumLedger') && creatorCode.includes('Журнал PVC'),
  'creator.js must expose the auditable Pivocoins ledger');
assert(creatorCode.includes('getCreatorPlayers') && creatorCode.includes('Список игроков'),
  'creator.js must expose searchable player-company administration');


const upgradesCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/upgrades.js'), 'utf-8');
assert(upgradesCode.includes('upgrade_options'), 'upgrades.js must render server-authoritative upgrade options');
assert(!upgradesCode.includes('calcUpgrade('), 'upgrades.js must not duplicate upgrade price formulas');
assert(upgradesCode.includes('upgrade-help-btn'), 'blocked upgrades must link to relevant help');

const productionCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/production.js'), 'utf-8');
assert(productionCode.includes('production-help-btn'), 'empty production must link to relevant help');
assert(productionCode.includes('start_hint') && productionCode.includes('factory-next-step'), 'factory cards must show the server-derived next step');

const catalogCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/catalog.js'), 'utf-8');
assert(catalogCode.includes('data-cat="unavailable"'), 'catalog.js must expose unavailable filter');
assert(catalogCode.includes('flex-wrap'), 'catalog filters must wrap instead of hiding actions beyond a narrow mobile viewport');

const appCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/app.js'), 'utf-8');
assert(!appCode.includes('Откройте НАТБИРЖУ из Telegram'),
  'Natbirzha must not block browser guests behind the Telegram-only screen');
assert(appCode.includes("msgText === '[object Object]'"), 'app.js showToast must guard against [object Object]');
assert(appCode.includes('window.NatApp'), 'app.js must expose window.NatApp');
assert(appCode.includes('navigateTo'), 'app.js must export navigateTo');
assert(appCode.includes('activeRenderPromise'), 'app.js must serialize overlapping async screen renders');
assert(appCode.includes('renderRequested'), 'app.js must coalesce rapid tab switches to the latest tab');
assert(appCode.includes('navigationId') && appCode.includes('AbortController'), 'app.js must cancel stale navigation requests');
assert(appCode.includes('renderContainer') && appCode.includes('container.replaceChildren(renderContainer)'), 'a stale screen must render off-DOM before it can be mounted');
assert(apiScript.includes('setNavigationAbortSignal'), 'api.js must attach the active navigation abort signal to requests');
assert(apiScript.includes("getRecipes: () => cachedGet") && apiScript.includes("getBuildingsCatalog: () => cachedGet"), 'Recipes and enterprise catalog must be cached');
assert(marketCode.includes('orderbookRequestId') && marketCode.includes('requestId !== orderbookRequestId'), 'Market must ignore a slow orderbook response for an older resource');
assert(appCode.includes('user?.is_creator === true'), 'creator UI must rely on server-provided creator flag');
assert(!appCode.includes('1053722876'), 'creator UI must not hardcode privileged Telegram IDs');

const commonAppCode = fs.readFileSync(path.join(__dirname, '../frontend/js/app.js'), 'utf-8');
assert(commonAppCode.includes('me.is_tester || me.role === "admin"'),
  'common Mini App must expose Natbirzha to the effective configured admin role');
assert(commonAppCode.includes('prepareNatbirzhaNavigation'),
  'common Mini App must provide prepareNatbirzhaNavigation');
console.log('All screen modules and app.js integration verified!');

console.log('=== [Natbirzha Test 5/5] Testing games.js Natbirzha banner exposure & items localization ===');
const gamesCode = fs.readFileSync(path.join(__dirname, '../frontend/js/games.js'), 'utf-8');
assert(gamesCode.includes('НАТБИРЖА'), 'games.js must contain Natbirzha banner definition');
assert(gamesCode.includes('${isTesterUser ?'), 'games.js must condition Natbirzha banner on isTesterUser');
assert(gamesCode.includes('/app/natbirzha'), 'Natbirzha banner must link to /app/natbirzha');
assert(gamesCode.includes('prepareNatbirzhaNavigation'),
  'Natbirzha banner must call prepareNatbirzhaNavigation to carry over Telegram auth');

const itemsScript = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/items.js'), 'utf-8');
const cleanedItemsScript = itemsScript.replace(/export\s+const\s+ITEMS\s+=/, 'const ITEMS =').replace(/export\s+function\s+getItemInfo/, 'function getItemInfo');
const itemsFn = new Function(cleanedItemsScript + '\nreturn { ITEMS, getItemInfo };');
const { ITEMS, getItemInfo } = itemsFn();
assert(ITEMS.water && ITEMS.water.name === 'Техническая вода', 'water must map to Russian name');
assert(ITEMS.grid_quota && ITEMS.grid_quota.name === 'Квота энергосети', 'grid_quota must map to Russian name');
assert(ITEMS.steel && ITEMS.steel.name === 'Конструкционная сталь', 'steel must map to Russian name');
assert(getItemInfo('WATER').name === 'Техническая вода', 'getItemInfo must be case-insensitive');
assert(getItemInfo('UNKNOWN_X').icon === '📦', 'getItemInfo must have safe fallback');

const overviewCode = fs.readFileSync(path.join(__dirname, '../frontend/natbirzha/js/screens/overview.js'), 'utf-8');
assert(overviewCode.includes('getItemInfo'), 'overview.js must use getItemInfo for warehouse items');
console.log('Natbirzha banner in games.js and items.js localization verified!');

console.log('\n🌟 ALL NATBIRZHA FRONTEND TESTS PASSED WITH 100% SUCCESS! 🌟');
