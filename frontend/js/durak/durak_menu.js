/**
 * durak_menu.js — Меню, выбор ставок, рейтинг и лобби для игры «Дурак».
 * Экспортирует window.DURAK_MENU = { showMenu, showLeaderboard, showOnlineMenu, renderWaiting }
 */
(function () {
  'use strict';

  function showMenu(container, ctx) {
    const coins = ctx.getUserCoins();
    let selectedStake = ctx.getSelectedStake();
    if (selectedStake > coins) {
      selectedStake = coins;
      ctx.setSelectedStake(selectedStake);
    }

    container.innerHTML = `
      <div class="dk-menu">
        <div class="dk-menu__title">🃏 Дурак</div>
        <div class="dk-menu__subtitle">Классическая карточная игра 11 «Б»</div>

        <!-- Баланс монет -->
        <div class="dk-coins-badge">
          🪙 Баланс: <b>${coins}</b> монет
        </div>

        <!-- Блок выбора ставки -->
        <div class="dk-stake-box">
          <div class="dk-stake-header">
            <span class="dk-stake-title">Ставка на игру:</span>
            <span class="dk-stake-val" id="dk-stake-val">${selectedStake} 🪙</span>
          </div>

          <!-- Быстрые пресеты -->
          <div class="dk-stake-group" id="dk-stake-group">
            <button type="button" class="dk-stake-opt ${selectedStake === 0 ? 'active' : ''}" data-val="0">Без ставки</button>
            <button type="button" class="dk-stake-opt ${selectedStake === 10 ? 'active' : ''}" data-val="10">10</button>
            <button type="button" class="dk-stake-opt ${selectedStake === 25 ? 'active' : ''}" data-val="25">25</button>
            <button type="button" class="dk-stake-opt ${selectedStake === 50 ? 'active' : ''}" data-val="50">50</button>
            <button type="button" class="dk-stake-opt ${selectedStake === 100 ? 'active' : ''}" data-val="100">100</button>
          </div>

          <!-- Произвольная ставка и Ва-банк -->
          <div class="dk-custom-stake-wrap">
            <div class="dk-input-with-icon">
              <span class="dk-input-icon">🪙</span>
              <input 
                type="number" 
                id="dk-custom-stake-input" 
                class="dk-stake-input" 
                placeholder="Своя ставка..." 
                min="0" 
                max="${coins}" 
                value="${selectedStake > 0 ? selectedStake : ''}" 
              />
            </div>
            <button type="button" class="dk-btn-all-in" id="dk-stake-all-in" title="Поставить все монеты">
              🔥 Ва-банк
            </button>
          </div>
          <div class="dk-stake-hint" id="dk-stake-hint">
            ${coins === 0 ? 'У вас 0 монет (игра доступна без ставки)' : `Доступно для ставки: ${coins} 🪙`}
          </div>
        </div>

        <!-- Режимы игры -->
        <button class="dk-btn dk-btn--primary" id="dk-mode-bot">🤖 Против бота</button>
        <button class="dk-btn dk-btn--primary" id="dk-mode-online">👥 Онлайн комната</button>
        
        <div class="dk-menu__room-join" style="display:flex; gap:8px; width:100%; max-width:280px;">
          <input class="dk-input" id="dk-join-id" placeholder="Код комнаты" style="flex:1;" />
          <button class="dk-btn" id="dk-join-btn" style="background:#0284c7; color:#fff; padding:8px 14px;">Вступить</button>
        </div>

        <button class="dk-btn dk-btn--leaderboard" id="dk-open-leaderboard">🏆 Рейтинг богачей</button>
      </div>`;

    const stakeValEl = container.querySelector('#dk-stake-val');
    const stakeInputEl = container.querySelector('#dk-custom-stake-input');
    const presetBtns = container.querySelectorAll('.dk-stake-opt');

    function syncStake(val, fromInput = false) {
      let num = parseInt(val, 10);
      if (isNaN(num) || num < 0) num = 0;
      if (num > coins) num = coins;

      ctx.setSelectedStake(num);
      if (stakeValEl) stakeValEl.textContent = `${num} 🪙`;

      presetBtns.forEach(btn => {
        const pval = parseInt(btn.dataset.val, 10);
        if (pval === num) btn.classList.add('active');
        else btn.classList.remove('active');
      });

      if (!fromInput && stakeInputEl) {
        stakeInputEl.value = num > 0 ? num : '';
      }
    }

    presetBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        syncStake(btn.dataset.val, false);
      });
    });

    if (stakeInputEl) {
      stakeInputEl.addEventListener('input', (e) => {
        syncStake(e.target.value, true);
      });
      stakeInputEl.addEventListener('change', (e) => {
        syncStake(e.target.value, false);
      });
    }

    const allInBtn = container.querySelector('#dk-stake-all-in');
    if (allInBtn) {
      allInBtn.addEventListener('click', () => {
        syncStake(coins, false);
      });
    }

    container.querySelector('#dk-mode-bot').addEventListener('click', () => {
      if (ctx.getSelectedStake() > coins) {
        alert(`Недостаточно монет! Ваш баланс: ${coins} 🪙`);
        return;
      }
      ctx.startBotGame();
    });

    container.querySelector('#dk-mode-online').addEventListener('click', () => {
      if (ctx.getSelectedStake() > coins) {
        alert(`Недостаточно монет! Ваш баланс: ${coins} 🪙`);
        return;
      }
      showOnlineMenu(container, ctx);
    });

    container.querySelector('#dk-join-btn').addEventListener('click', () => {
      const rid = container.querySelector('#dk-join-id').value.trim();
      if (rid) ctx.joinRoom(rid);
    });

    container.querySelector('#dk-open-leaderboard').addEventListener('click', () => {
      showLeaderboard(container, ctx);
    });
  }

  async function showLeaderboard(container, ctx) {
    container.innerHTML = `
      <div class="dk-menu">
        <div class="dk-menu__title">🏆 Рейтинг богачей</div>
        <div class="dk-menu__subtitle">Топ учеников по количеству монет</div>
        <div id="dk-leaderboard-list" class="dk-leaderboard-box">
          <div class="dk-loading" style="padding:20px; color:#64748b; font-size:0.85rem;">Загрузка рейтинга...</div>
        </div>
        <button class="dk-btn" id="dk-leaderboard-back" style="background:#e2e8f0; color:#1e293b;">← Назад к игре</button>
      </div>`;

    container.querySelector('#dk-leaderboard-back').addEventListener('click', () => {
      showMenu(container, ctx);
    });

    try {
      const res = await ctx.apiGet('/api/durak/leaderboard');
      const leaders = res.leaderboard || [];
      const listEl = container.querySelector('#dk-leaderboard-list');
      if (!leaders.length) {
        listEl.innerHTML = '<div style="color:#888; font-size:0.85rem; padding:16px;">Пока никто не включил игровую экосистему</div>';
        return;
      }
      const myUid = ctx.getUserId();
      listEl.innerHTML = leaders.map(l => {
        let medal = `#${l.rank}`;
        if (l.rank === 1) medal = '🥇 1';
        if (l.rank === 2) medal = '🥈 2';
        if (l.rank === 3) medal = '🥉 3';
        const uname = l.username ? `<span class="dk-lead-uname">@${l.username}</span>` : '';
        return `
          <div class="dk-lead-row ${l.tg_id === myUid ? 'dk-lead-row--me' : ''}">
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

  function showOnlineMenu(container, ctx) {
    const stake = ctx.getSelectedStake();
    container.innerHTML = `
      <div class="dk-menu">
        <div class="dk-menu__title">👥 Онлайн «Дурак»</div>
        <div class="dk-coins-badge">Ставка: <b>${stake}</b> 🪙 (с каждого игрока)</div>
        <label class="dk-label">Количество игроков:
          <select class="dk-select" id="dk-players-count">
            <option value="2">2 игрока</option>
            <option value="3">3 игрока</option>
            <option value="4">4 игрока</option>
            <option value="5">5 игроков</option>
            <option value="6">6 игроков</option>
          </select>
        </label>
        <button class="dk-btn dk-btn--primary" id="dk-create-online">Создать комнату</button>
        <button class="dk-btn" id="dk-back-menu" style="background:#e2e8f0; color:#1e293b;">← Назад</button>
      </div>`;

    container.querySelector('#dk-create-online').addEventListener('click', async () => {
      const cnt = parseInt(container.querySelector('#dk-players-count').value, 10);
      ctx.createOnlineRoom(cnt, stake);
    });

    container.querySelector('#dk-back-menu').addEventListener('click', () => {
      showMenu(container, ctx);
    });
  }

  function renderWaiting(container, roomId, players, stake, onCancel) {
    if (!container) return;
    const stakeText = stake > 0 ? `<div class="dk-waiting__stake">💰 Ставка: <b>${stake} 🪙</b></div>` : '';
    container.innerHTML = `
      <div class="dk-waiting">
        <div class="dk-waiting__title">⏳ Ожидание игроков…</div>
        <div class="dk-waiting__count">Подключено: ${players.length}</div>
        ${stakeText}
        <div class="dk-waiting__hint">Поделитесь кодом комнаты: <b>${roomId}</b></div>
        <button class="dk-btn dk-btn--exit" id="dk-cancel-room">✕ Отменить комнату</button>
      </div>`;

    const cancelBtn = container.querySelector('#dk-cancel-room');
    if (cancelBtn && onCancel) {
      cancelBtn.addEventListener('click', onCancel);
    }
  }

  window.DURAK_MENU = { showMenu, showLeaderboard, showOnlineMenu, renderWaiting };
})();
