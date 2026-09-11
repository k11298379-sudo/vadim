/**
 * durak.js — UI игры «Дурак» для Mini App.
 *
 * Экспортирует window.DURAK = { init, destroy }
 * Вызывается из games.js при выборе игры «Дурак».
 */
(function () {
  'use strict';

  // ─── Константы ───────────────────────────────────────────────────────────────
  const SUIT_COLOR = { '♠': '#1a1a2e', '♣': '#16213e', '♥': '#e94560', '♦': '#e94560' };
  const RANK_LABELS = { J: 'J', Q: 'Q', K: 'K', A: 'A' };

  // ─── Состояние ───────────────────────────────────────────────────────────────
  let _roomId = null;
  let _userId = null;
  let _ws = null;
  let _state = null;  // последнее состояние от сервера
  let _selectedCard = null;   // карта, выбранная для хода (объект {suit,rank})
  let _container = null;
  let _selectedStake = 0;
  let _userCoins = 0;

  // ─── Утилиты ─────────────────────────────────────────────────────────────────

  function getUserId() {
    if (_userId) return _userId;
    if (window.currentUser && window.currentUser.tg_id) return window.currentUser.tg_id;
    const params = new URLSearchParams(window.location.search);
    return parseInt(params.get('user_id') || params.get('uid') || '0', 10);
  }

  function apiBase() {
    return window.location.origin;
  }

  async function apiPost(path, body = {}) {
    const uid = getUserId();
    const resp = await fetch(`${apiBase()}${path}?user_id=${uid}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, user_id: uid }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
  }

  async function apiGet(path) {
    const uid = getUserId();
    const resp = await fetch(`${apiBase()}${path}?user_id=${uid}`);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
  }

  async function refreshUserCoins() {
    try {
      const me = await apiGet('/api/me');
      if (me && typeof me.coins !== 'undefined') {
        _userCoins = Number(me.coins || 0);
        if (window.currentUser) window.currentUser.coins = _userCoins;
      }
    } catch (e) {
      if (window.currentUser && typeof window.currentUser.coins !== 'undefined') {
        _userCoins = Number(window.currentUser.coins || 0);
      }
    }
    return _userCoins;
  }

  // ─── WebSocket ───────────────────────────────────────────────────────────────

  function connectWS() {
    if (_ws) { _ws.close(); _ws = null; }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const uid = getUserId();
    const url = `${protocol}//${window.location.host}/api/ws/durak/${_roomId}/${uid}`;

    try {
      _ws = new WebSocket(url);
    } catch (e) {
      console.warn('WS connect failed, falling back to polling', e);
      return;
    }

    _ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'state') {
          _state = data.state;
          renderGame();
        } else if (data.type === 'waiting') {
          renderWaiting(data.players, data.stake || _selectedStake);
        }
      } catch (e) { /* ignore */ }
    };

    _ws.onclose = () => {
      setTimeout(() => { if (_roomId) connectWS(); }, 3000);
    };

    const ping = setInterval(() => {
      if (_ws && _ws.readyState === WebSocket.OPEN) _ws.send('ping');
      else clearInterval(ping);
    }, 25000);
  }

  // ─── Карта ───────────────────────────────────────────────────────────────────

  const SUIT_NAME_MAP = { '♠': 'spades', '♣': 'clubs', '♥': 'hearts', '♦': 'diamonds' };

  function cardHTML(card, faceDown = false, selectable = false, selected = false) {
    if (faceDown) {
      return `
        <div class="dk-card dk-card--back">
          <img src="/static/img/cards/back.svg" class="dk-card__img" alt="Рубашка" />
        </div>`;
    }
    const suitName = SUIT_NAME_MAP[card.suit] || 'spades';
    const sel = selected ? ' dk-card--selected' : '';
    const cls = selectable ? ' dk-card--selectable' : '';
    const imgSrc = `/static/img/cards/${card.rank}_${suitName}.png`;

    return `
      <div class="dk-card${cls}${sel}" data-suit="${card.suit}" data-rank="${card.rank}">
        <img src="${imgSrc}" onerror="this.onerror=null;this.src='/static/img/cards/${card.rank}_${suitName}.svg'" class="dk-card__img" alt="${card.rank}${card.suit}" />
      </div>`;
  }

  function cardKey(card) { return `${card.suit}${card.rank}`; }

  // ─── Рендер ──────────────────────────────────────────────────────────────────

  function renderWaiting(players, stake = 0) {
    if (!_container) return;
    const stakeText = stake > 0 ? `<div class="dk-waiting__stake">💰 Ставка: <b>${stake} 🪙</b></div>` : '';
    _container.innerHTML = `
      <div class="dk-waiting">
        <div class="dk-waiting__title">⏳ Ожидание игроков…</div>
        <div class="dk-waiting__count">Подключено: ${players.length}</div>
        ${stakeText}
        <div class="dk-waiting__hint">Поделитесь кодом комнаты: <b>${_roomId}</b></div>
        <button class="dk-btn dk-btn--exit" id="dk-cancel-room">✕ Отменить комнату</button>
      </div>`;

    const cancelBtn = _container.querySelector('#dk-cancel-room');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', async () => {
        try {
          await apiPost('/api/durak/cancel', { room_id: _roomId });
        } catch (e) {}
        showMenu(_container);
      });
    }
  }

  function renderGame() {
    if (!_container || !_state) return;
    const s = _state;
    const uid = getUserId();
    const myHand = s.hands[String(uid)] || [];
    const isMyHandArray = Array.isArray(myHand);

    const phase = s.phase;
    const isAttacker = s.current_attacker === uid;
    const isDefender = s.current_defender === uid;
    const myTurn = isAttacker || isDefender;

    // ── Рука игрока
    let handHTML = '';
    if (isMyHandArray) {
      handHTML = myHand.map(c => {
        const isSelected = _selectedCard && cardKey(_selectedCard) === cardKey(c);
        const selectable = myTurn && !isGameOver(s);
        return cardHTML(c, false, selectable, isSelected);
      }).join('');
    }

    // ── Стол
    let tableHTML = '';
    for (const slot of s.table) {
      const atkCard = cardHTML(slot.attack, false);
      const defCard = slot.defend ? cardHTML(slot.defend, false) : `<div class="dk-card dk-card--empty">?</div>`;
      tableHTML += `<div class="dk-slot">${atkCard}<div class="dk-slot__arr">▼</div>${defCard}</div>`;
    }

    // ── Статус & Банк
    let statusText = '';
    if (isGameOver(s)) {
      refreshUserCoins();
      const pot = s.total_pot || (s.stake ? s.stake * 2 : 0);
      if (s.winner === uid) {
        statusText = s.stake > 0
          ? `🏆 <b>Вы победили!</b> Выигрыш: <b>+${pot} 🪙</b>`
          : '🏆 <b>Вы победили!</b>';
      } else if (s.loser === uid) {
        statusText = s.stake > 0
          ? `🃏 <b>Вы — дурак!</b> Потеряно: <b>-${s.stake} 🪙</b>`
          : '🃏 <b>Вы — дурак!</b>';
      } else {
        statusText = s.loser ? `🃏 Дурак: игрок ${s.loser}` : '🤝 Ничья!';
      }
    } else if (isAttacker) {
      statusText = phase === 'attack' ? '⚔️ Ваш ход — атакуйте' : '✅ Атака принята — можно подкинуть или передать ход';
    } else if (isDefender) {
      statusText = '🛡 Выберите карту для отбоя';
    } else {
      const whose = isAttacker ? 'вашего' : `игрока ${s.current_attacker}`;
      statusText = `⏳ Ожидание хода ${whose}`;
    }

    // ── Кнопки действий
    let actionsHTML = '';
    if (!isGameOver(s)) {
      if (isAttacker && phase === 'attack') {
        actionsHTML += `<button class="dk-btn dk-btn--attack" id="dk-btn-attack" ${!_selectedCard ? 'disabled' : ''}>⚔️ Атаковать</button>`;
      }
      if (isAttacker && phase === 'attack' && s.table.length > 0) {
        actionsHTML += `<button class="dk-btn dk-btn--pass" id="dk-btn-pass">🔄 Передать ход</button>`;
      }
      if (isDefender && phase === 'defend') {
        actionsHTML += `<button class="dk-btn dk-btn--defend" id="dk-btn-defend" ${!_selectedCard ? 'disabled' : ''}>🛡 Отбить</button>`;
        actionsHTML += `<button class="dk-btn dk-btn--take" id="dk-btn-take">📥 Взять</button>`;
      }
    } else {
      actionsHTML = `<button class="dk-btn dk-btn--new" id="dk-btn-new">🎮 В меню / Новая игра</button>`;
    }

    // ── Другие игроки
    let opponentsHTML = '';
    for (const pid of s.player_ids) {
      if (pid === uid) continue;
      const hand = s.hands[String(pid)];
      const count = Array.isArray(hand) ? hand.length : hand;
      const isBot = s.bot_indices.includes(pid);
      const label = isBot ? '🤖 Бот' : `Игрок ${pid}`;
      const isAtk = s.current_attacker === pid ? ' 🗡' : '';
      const isDef = s.current_defender === pid ? ' 🛡' : '';
      opponentsHTML += `<div class="dk-opponent">${label}${isAtk}${isDef}: ${count} карт</div>`;
    }

    // ── Козырь + колода + банк
    const trumpHTML = s.trump_card
      ? `<span style="color:${SUIT_COLOR[s.trump_card.suit]}">
           ${s.trump_card.rank}${s.trump_card.suit}
         </span>`
      : '—';

    const potBadge = s.stake > 0
      ? `<span class="dk-pot">💰 Банк: <b>${s.total_pot || s.stake * 2} 🪙</b></span>`
      : '';

    _container.innerHTML = `
      <div class="dk-game">
        <div class="dk-header">
          <span class="dk-trump">Козырь: ${trumpHTML}</span>
          ${potBadge}
          <span class="dk-deck">🂠 ${s.deck_count}</span>
          <button class="dk-btn dk-btn--exit" id="dk-btn-exit">✕ Выйти</button>
        </div>
        <div class="dk-opponents">${opponentsHTML}</div>
        <div class="dk-status">${statusText}</div>
        <div class="dk-table">${tableHTML || '<span class="dk-table__empty">Стол пуст</span>'}</div>
        <div class="dk-hand">${handHTML}</div>
        <div class="dk-actions">${actionsHTML}</div>
      </div>`;

    // ── Навешиваем обработчики
    _container.querySelectorAll('.dk-card--selectable').forEach(el => {
      el.addEventListener('click', () => onCardClick(el));
    });

    const btnAttack = _container.querySelector('#dk-btn-attack');
    if (btnAttack) btnAttack.addEventListener('click', doAttack);

    const btnDefend = _container.querySelector('#dk-btn-defend');
    if (btnDefend) btnDefend.addEventListener('click', doDefend);

    const btnTake = _container.querySelector('#dk-btn-take');
    if (btnTake) btnTake.addEventListener('click', doTake);

    const btnPass = _container.querySelector('#dk-btn-pass');
    if (btnPass) btnPass.addEventListener('click', doPass);

    const btnNew = _container.querySelector('#dk-btn-new');
    if (btnNew) btnNew.addEventListener('click', () => showMenu(_container));

    const btnExit = _container.querySelector('#dk-btn-exit');
    if (btnExit) btnExit.addEventListener('click', () => showMenu(_container));
  }

  function isGameOver(s) {
    return s && s.phase === 'done';
  }

  // ─── Действия ────────────────────────────────────────────────────────────────

  function onCardClick(el) {
    const suit = el.dataset.suit;
    const rank = el.dataset.rank;
    if (_selectedCard && _selectedCard.suit === suit && _selectedCard.rank === rank) {
      _selectedCard = null;
    } else {
      _selectedCard = { suit, rank };
    }
    renderGame();
  }

  async function doAttack() {
    if (!_selectedCard) return;
    await sendMove({ action: 'attack', card: _selectedCard });
  }

  async function doDefend() {
    if (!_selectedCard) return;
    const openSlot = _state.table.find(s => s.defend === null);
    if (!openSlot) return;
    await sendMove({
      action: 'defend',
      attack_card: openSlot.attack,
      card: _selectedCard,
    });
  }

  async function doTake() {
    await sendMove({ action: 'take' });
  }

  async function doPass() {
    await sendMove({ action: 'pass' });
  }

  async function sendMove(payload) {
    try {
      const res = await apiPost('/api/durak/move', { ...payload, room_id: _roomId });
      _selectedCard = null;
      _state = res.state;
      renderGame();
    } catch (e) {
      showError(e.message);
    }
  }

  function showError(msg) {
    const el = _container && _container.querySelector('.dk-status');
    if (el) {
      el.textContent = `⚠️ ${msg}`;
      el.style.color = '#e94560';
      setTimeout(() => renderGame(), 2500);
    }
  }

  // ─── Меню выбора режима ───────────────────────────────────────────────────────

  async function showMenu(container) {
    _roomId = null;
    _selectedCard = null;
    _state = null;
    if (_ws) { _ws.close(); _ws = null; }

    await refreshUserCoins();

    container.innerHTML = `
      <div class="dk-menu">
        <div class="dk-menu__title">🃏 Дурак</div>

        <!-- Баланс монет -->
        <div class="dk-coins-badge">
          🪙 Баланс: <b>${_userCoins}</b> монет
        </div>

        <!-- Блок выбора ставки -->
        <div class="dk-stake-box">
          <span class="dk-stake-title">Ставка на игру:</span>
          <div class="dk-stake-group" id="dk-stake-group">
            <button class="dk-stake-opt ${_selectedStake === 0 ? 'active' : ''}" data-val="0">0</button>
            <button class="dk-stake-opt ${_selectedStake === 10 ? 'active' : ''}" data-val="10">10</button>
            <button class="dk-stake-opt ${_selectedStake === 25 ? 'active' : ''}" data-val="25">25</button>
            <button class="dk-stake-opt ${_selectedStake === 50 ? 'active' : ''}" data-val="50">50</button>
            <button class="dk-stake-opt ${_selectedStake === 100 ? 'active' : ''}" data-val="100">100</button>
          </div>
        </div>

        <button class="dk-btn dk-btn--primary" id="dk-mode-bot">🤖 Против бота</button>
        <button class="dk-btn dk-btn--primary" id="dk-mode-online">👥 Онлайн комната</button>
        
        <div class="dk-menu__room-join">
          <input class="dk-input" id="dk-join-id" placeholder="Код комнаты" />
          <button class="dk-btn" id="dk-join-btn">Вступить</button>
        </div>

        <button class="dk-btn dk-btn--leaderboard" id="dk-open-leaderboard">🏆 Рейтинг богачей</button>
      </div>`;

    // Переключение ставок
    container.querySelectorAll('.dk-stake-opt').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.dk-stake-opt').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        _selectedStake = parseInt(btn.dataset.val || '0', 10);
      });
    });

    container.querySelector('#dk-mode-bot').addEventListener('click', () => startBotGame(container));
    container.querySelector('#dk-mode-online').addEventListener('click', () => showOnlineMenu(container));
    container.querySelector('#dk-join-btn').addEventListener('click', () => {
      const rid = container.querySelector('#dk-join-id').value.trim();
      if (rid) joinRoom(container, rid);
    });
    container.querySelector('#dk-open-leaderboard').addEventListener('click', () => showLeaderboard(container));
  }

  async function showLeaderboard(container) {
    container.innerHTML = `
      <div class="dk-menu">
        <div class="dk-menu__title">🏆 Рейтинг богачей</div>
        <div class="dk-menu__subtitle">Топ учеников по количеству монет</div>
        <div id="dk-leaderboard-list" class="dk-leaderboard-box">
          <div class="dk-loading">Загрузка рейтинга...</div>
        </div>
        <button class="dk-btn" id="dk-leaderboard-back">← Назад к игре</button>
      </div>`;

    container.querySelector('#dk-leaderboard-back').addEventListener('click', () => showMenu(container));

    try {
      const res = await apiGet('/api/durak/leaderboard');
      const leaders = res.leaderboard || [];
      const listEl = container.querySelector('#dk-leaderboard-list');
      if (!leaders.length) {
        listEl.innerHTML = '<div style="color:#888; font-size:0.85rem; padding:16px;">Пока никто не включил игровую экосистему</div>';
        return;
      }
      listEl.innerHTML = leaders.map(l => {
        let medal = `#${l.rank}`;
        if (l.rank === 1) medal = '🥇 1';
        if (l.rank === 2) medal = '🥈 2';
        if (l.rank === 3) medal = '🥉 3';
        const uname = l.username ? `<span class="dk-lead-uname">@${l.username}</span>` : '';
        return `
          <div class="dk-lead-row ${l.tg_id === getUserId() ? 'dk-lead-row--me' : ''}">
            <span class="dk-lead-rank">${medal}</span>
            <div class="dk-lead-info">
              <span class="dk-lead-name">${l.name}</span>
              ${uname}
            </div>
            <span class="dk-lead-coins">${l.coins} 🪙</span>
          </div>`;
      }).join('');
    } catch (e) {
      const listEl = container.querySelector('#dk-leaderboard-list');
      if (listEl) listEl.innerHTML = `<div class="dk-error">Ошибка: ${e.message}</div>`;
    }
  }

  async function startBotGame(container) {
    _userId = getUserId();
    try {
      const res = await apiPost('/api/durak/new', { mode: 'bot', players_count: 2, stake: _selectedStake });
      _roomId = res.room_id;
      _state = res.state;
      connectWS();
      renderGame();
    } catch (e) {
      alert(`Ошибка: ${e.message}`);
    }
  }

  function showOnlineMenu(container) {
    container.innerHTML = `
      <div class="dk-menu">
        <div class="dk-menu__title">👥 Онлайн «Дурак»</div>
        <div class="dk-coins-badge">Ставка: <b>${_selectedStake}</b> 🪙 (с каждого игрока)</div>
        <label class="dk-label">Количество игроков:
          <select class="dk-select" id="dk-players-count">
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
            <option value="6">6</option>
          </select>
        </label>
        <button class="dk-btn dk-btn--primary" id="dk-create-online">Создать комнату</button>
        <button class="dk-btn" id="dk-back-menu">← Назад</button>
      </div>`;

    container.querySelector('#dk-create-online').addEventListener('click', async () => {
      _userId = getUserId();
      const cnt = parseInt(container.querySelector('#dk-players-count').value, 10);
      try {
        const res = await apiPost('/api/durak/new', { mode: 'online', players_count: cnt, stake: _selectedStake });
        _roomId = res.room_id;
        connectWS();
        renderWaiting(res.players, _selectedStake);
      } catch (e) {
        alert(`Ошибка: ${e.message}`);
      }
    });

    container.querySelector('#dk-back-menu').addEventListener('click', () => showMenu(container));
  }

  async function joinRoom(container, roomId) {
    _userId = getUserId();
    _roomId = roomId;
    try {
      const res = await apiPost('/api/durak/join', { room_id: roomId });
      connectWS();
      if (res.status === 'started') {
        _state = res.state;
        renderGame();
      } else {
        renderWaiting(res.players, res.stake || 0);
      }
    } catch (e) {
      alert(`Ошибка: ${e.message}`);
    }
  }

  // ─── CSS ─────────────────────────────────────────────────────────────────────

  function injectCSS() {
    if (document.getElementById('durak-css')) return;
    const style = document.createElement('style');
    style.id = 'durak-css';
    style.textContent = `
      .dk-menu { display:flex; flex-direction:column; align-items:center; gap:12px; padding:20px 16px; }
      .dk-menu__title { font-size:1.8rem; font-weight:800; }
      .dk-menu__subtitle { color:#888; margin-bottom:6px; font-size:0.85rem; }
      .dk-coins-badge { background:rgba(234, 179, 8, 0.15); border:1px solid rgba(234, 179, 8, 0.4); color:#b45309; padding:6px 14px; border-radius:12px; font-size:0.9rem; font-weight:700; }
      
      .dk-stake-box { display:flex; flex-direction:column; align-items:center; gap:6px; background:rgba(0,0,0,0.03); border:1px solid rgba(0,0,0,0.06); padding:10px 14px; border-radius:14px; width:100%; max-width:280px; }
      .dk-stake-title { font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; }
      .dk-stake-group { display:flex; gap:6px; justify-content:center; }
      .dk-stake-opt { padding:6px 10px; border-radius:8px; border:1px solid #cbd5e1; background:#fff; font-size:0.8rem; font-weight:700; cursor:pointer; transition:all 0.15s; }
      .dk-stake-opt.active { background:#2563eb; color:#fff; border-color:#2563eb; }

      .dk-pot { background:rgba(234, 179, 8, 0.2); border:1px solid #facc15; color:#854d0e; padding:3px 8px; border-radius:8px; font-size:0.8rem; font-weight:800; }

      .dk-leaderboard-box { width:100%; max-width:320px; display:flex; flex-direction:column; gap:6px; max-height:260px; overflow-y:auto; padding:4px; }
      .dk-lead-row { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:rgba(0,0,0,0.03); border-radius:10px; font-size:0.85rem; }
      .dk-lead-row--me { background:rgba(37, 99, 235, 0.1); border:1px solid rgba(37, 99, 235, 0.3); }
      .dk-lead-rank { font-weight:800; width:45px; }
      .dk-lead-info { display:flex; flex-direction:column; flex:1; text-align:left; }
      .dk-lead-name { font-weight:700; }
      .dk-lead-uname { font-size:0.7rem; color:#64748b; }
      .dk-lead-coins { font-weight:800; color:#b45309; }

      .dk-game { display:flex; flex-direction:column; height:100%; padding:8px; gap:8px; }
      .dk-header { display:flex; align-items:center; gap:8px; font-size:.9rem; }
      .dk-trump { font-weight:600; flex:1; }
      .dk-deck { font-weight:600; }
      .dk-status { text-align:center; font-size:.9rem; font-weight:600; padding:6px; background:rgba(0,0,0,.05); border-radius:8px; }
      .dk-opponents { display:flex; flex-wrap:wrap; gap:6px; justify-content:center; }
      .dk-opponent { font-size:.8rem; background:rgba(0,0,0,.06); border-radius:8px; padding:4px 10px; }
      .dk-table { min-height:90px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; justify-content:center;
                  background:rgba(0,120,60,.08); border-radius:12px; padding:8px; }
      .dk-table__empty { color:#aaa; font-size:.85rem; }
      .dk-slot { display:flex; flex-direction:column; align-items:center; gap:2px; }
      .dk-slot__arr { font-size:.7rem; color:#aaa; }
      .dk-hand { display:flex; flex-wrap:wrap; gap:6px; justify-content:center; padding:6px 0; min-height:80px; }
      .dk-actions { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; padding:4px 0; }

      /* Карта */
      .dk-card { width:58px; height:82px; border-radius:8px; display:inline-flex;
                 align-items:center; justify-content:center; user-select:none;
                 position:relative; transition:transform .15s ease, filter .15s ease; }
      .dk-card__img { width:100%; height:100%; object-fit:contain; pointer-events:none; border-radius:8px; }
      .dk-card--back { width:58px; height:82px; }
      .dk-card--empty { width:58px; height:82px; background:rgba(0,0,0,.04); border:2px dashed #cbd5e1;
                        border-radius:8px; color:#94a3b8; font-size:1.5rem; display:flex;
                        align-items:center; justify-content:center; }
      .dk-card--selectable { cursor:pointer; }
      .dk-card--selectable:hover { transform:translateY(-6px); filter:drop-shadow(0 6px 14px rgba(0,0,0,.22)); }
      .dk-card--selected { transform:translateY(-10px); filter:drop-shadow(0 8px 18px rgba(225,29,72,.45)); }

      /* Кнопки */
      .dk-btn { padding:10px 18px; border:none; border-radius:10px; cursor:pointer;
                font-size:.9rem; font-weight:600; transition:opacity .15s; }
      .dk-btn:disabled { opacity:.4; cursor:not-allowed; }
      .dk-btn--primary { background:#2563eb; color:#fff; width:100%; max-width:280px; }
      .dk-btn--leaderboard { background:#f59e0b; color:#fff; width:100%; max-width:280px; }
      .dk-btn--attack { background:#e94560; color:#fff; }
      .dk-btn--defend { background:#16a34a; color:#fff; }
      .dk-btn--take { background:#ca8a04; color:#fff; }
      .dk-btn--pass { background:#6b7280; color:#fff; }
      .dk-btn--new { background:#7c3aed; color:#fff; }
      .dk-btn--exit { background:none; border:1.5px solid #ddd; color:#666; padding:6px 12px; font-size:.8rem; }
      .dk-input { border:1.5px solid #ddd; border-radius:8px; padding:8px 12px; font-size:.9rem; width:140px; }
      .dk-select { border:1.5px solid #ddd; border-radius:8px; padding:6px 10px; font-size:.9rem; }
      .dk-label { font-size:.9rem; display:flex; align-items:center; gap:8px; }
      .dk-error { padding:24px; text-align:center; color:#e94560; font-weight:600; }
      .dk-waiting { display:flex; flex-direction:column; align-items:center; gap:12px; padding:32px; }
      .dk-waiting__title { font-size:1.4rem; font-weight:700; }
      .dk-waiting__count { color:#888; }
      .dk-waiting__stake { color:#b45309; font-weight:700; font-size:1rem; }
      .dk-waiting__hint { background:rgba(0,0,0,.05); border-radius:8px; padding:10px 16px; font-size:.85rem; }
    `;
    document.head.appendChild(style);
  }

  // ─── Публичный API ────────────────────────────────────────────────────────────

  function init(container) {
    _container = container;
    _roomId = null;
    _state = null;
    _selectedCard = null;
    _userId = getUserId();
    injectCSS();
    showMenu(container);
  }

  function destroy() {
    if (_ws) { _ws.close(); _ws = null; }
    _roomId = null;
    _state = null;
    _selectedCard = null;
    _container = null;
  }

  window.DURAK = { init, destroy };
})();
