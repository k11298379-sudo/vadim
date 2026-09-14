// МОДУЛЬ МИНИ-ИГР ДЛЯ MINI APP — КООРДИНАТОР И РОУТЕР
(function () {
  'use strict';

  let currentGame = "2048"; // 'rpg', '2048', 'tictactoe', 'snake', 'tetris', 'chess', 'durak'
  window.currentGame = currentGame;
  let isTesterUser = false;
  let isCurrencyEnabled = false;
  let userCoins = 0;
  let testerChecked = false;

  async function checkTesterStatus() {
    try {
      const sParams = new URLSearchParams(window.location.search);
      if (sParams.has("tester")) {
        const val = sParams.get("tester");
        isTesterUser = val === "1" || val === "true";
        try { localStorage.setItem("is_tester", isTesterUser ? "1" : "0"); } catch (e) {}
      } else if (sParams.get("role") === "tester" || localStorage.getItem("is_tester") === "1") {
        isTesterUser = true;
      }
    } catch (e) {}

    if (window.currentUser && typeof window.currentUser.is_tester !== "undefined") {
      isTesterUser = Boolean(window.currentUser.is_tester);
      isCurrencyEnabled = Boolean(window.currentUser.currency_ecosystem_enabled);
      userCoins = Number(window.currentUser.coins || 0);
      testerChecked = true;
      return isTesterUser;
    }

    try {
      const apiObj = window.api || (typeof api !== "undefined" ? api : null);
      const me = (apiObj && typeof apiObj.getMe === "function") ? await apiObj.getMe() : null;
      if (me) {
        window.currentUser = me;
        isTesterUser = Boolean(me.is_tester);
        isCurrencyEnabled = Boolean(me.currency_ecosystem_enabled);
        userCoins = Number(me.coins || 0);
        try { localStorage.setItem("is_tester", isTesterUser ? "1" : "0"); } catch (e) {}
      }
    } catch (e) {}

    testerChecked = true;
    return isTesterUser;
  }

  function updateTesterStatus(isTester) {
    const wasTester = isTesterUser;
    isTesterUser = Boolean(isTester);
    testerChecked = true;
    try {
      localStorage.setItem("is_tester", isTesterUser ? "1" : "0");
    } catch (e) {}
    const container = document.getElementById("pane-games");
    if (container && wasTester !== isTesterUser) {
      renderGames();
    }
  }

  async function initGames() {
    const container = document.getElementById("pane-games");
    if (!container) return;
    await checkTesterStatus();
    if (isTesterUser && currentGame === "2048") {
      currentGame = "rpg";
    }
    window.currentGame = currentGame;
    renderGames();
  }

  function renderGames() {
    const container = document.getElementById("pane-games");
    if (!container) return;

    window.currentGame = currentGame;

    const baseGames = [
      { id: "2048", icon: "🔢", name: "2048", color: "blue" },
      { id: "tictactoe", icon: "❌⭕", name: "Крестики", color: "blue" },
      { id: "snake", icon: "🐍", name: "Змейка", color: "blue" },
      { id: "tetris", icon: "🧱", name: "Тетрис", color: "blue" },
      { id: "chess", icon: "♟️", name: "Шахматы", color: "blue" },
      { id: "durak", icon: "🃏", name: "Дурак", color: "red" },
    ];
    const gamesList = isTesterUser
      ? [{ id: "rpg", icon: "⚔️", name: "natarGRP", color: "amber" }, ...baseGames]
      : baseGames;

    const gameCountLabel = `${gamesList.length} игр${isTesterUser ? ' (⚔️ natarGRP)' : ''}`;

    const tabsHTML = gamesList.map(g => {
      const isCur = currentGame === g.id;
      let activeColor = "text-blue-600 dark:text-blue-400";
      if (g.color === "amber") activeColor = "text-amber-600 dark:text-amber-400";
      else if (g.color === "red") activeColor = "text-red-600 dark:text-red-400";
      const activeClass = isCur
        ? `bg-white dark:bg-slate-700 ${activeColor} shadow-sm`
        : "text-slate-500 dark:text-slate-400 hover:text-slate-700";
      return `
        <button onclick="window.GAMES.switchGame('${g.id}')" class="py-2 rounded-xl transition-all flex items-center justify-center gap-1 ${activeClass}">
          <span>${g.icon}</span>
          <span class="truncate">${g.name}</span>
        </button>
      `;
    }).join("");

    container.innerHTML = `
      <!-- Header -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-base font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-1.5">
              <span>🎮</span> Мини-игры
            </h2>
            <p class="text-xs text-slate-400 font-medium">Отдохни на перемене с пользой для ума</p>
          </div>
          <span class="text-[11px] font-bold px-2 py-0.5 rounded-lg bg-amber-50 dark:bg-slate-800 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-slate-700">${gameCountLabel}</span>
        </div>

        <!-- Games selector tabs -->
        <div class="gap-1 p-1 rounded-2xl bg-slate-200/70 dark:bg-slate-800/90 text-[10px] font-bold" style="display: grid; grid-template-columns: repeat(${gamesList.length}, minmax(0, 1fr));">
          ${tabsHTML}
        </div>
      </div>

      <!-- Game Canvas / Container -->
      <div id="game-active-container" class="pt-1">
        ${renderActiveGame()}
      </div>
    `;

    // After DOM update, initialize specific game listeners
    if (currentGame === "rpg") {
      if (window.RPG && typeof window.RPG.init === "function") window.RPG.init();
    } else if (currentGame === "2048") {
      if (window.GAMES_2048) window.GAMES_2048.init();
    } else if (currentGame === "tictactoe") {
      if (window.GAMES_TICTACTOE) window.GAMES_TICTACTOE.init();
    } else if (currentGame === "snake") {
      if (window.GAMES_SNAKE) window.GAMES_SNAKE.init();
    } else if (currentGame === "tetris") {
      if (window.GAMES_TETRIS) window.GAMES_TETRIS.init();
    } else if (currentGame === "chess") {
      if (window.GAMES_CHESS) window.GAMES_CHESS.init();
    } else if (currentGame === "durak") {
      initDurak();
    }
  }

  function switchGame(gameId) {
    cleanupCurrentGame();
    currentGame = gameId;
    window.currentGame = gameId;
    renderGames();
  }

  function cleanupCurrentGame() {
    if (window.RPG) {
      if (typeof window.RPG.leavePvPRoom === "function") window.RPG.leavePvPRoom();
      if (typeof window.RPG.leaveCoopRoom === "function") window.RPG.leaveCoopRoom();
    }
    if (window.GAMES_2048 && typeof window.GAMES_2048.cleanup === 'function') {
      window.GAMES_2048.cleanup();
    }
    if (window.GAMES_TICTACTOE && typeof window.GAMES_TICTACTOE.cleanup === 'function') {
      window.GAMES_TICTACTOE.cleanup();
    }
    if (window.GAMES_SNAKE && typeof window.GAMES_SNAKE.cleanup === 'function') {
      window.GAMES_SNAKE.cleanup();
    }
    if (window.GAMES_TETRIS && typeof window.GAMES_TETRIS.cleanup === 'function') {
      window.GAMES_TETRIS.cleanup();
    }
    if (window.GAMES_CHESS && typeof window.GAMES_CHESS.cleanup === 'function') {
      window.GAMES_CHESS.cleanup();
    }
    if (window.DURAK && typeof window.DURAK.destroy === 'function') {
      window.DURAK.destroy();
    }
  }

  function renderActiveGame() {
    if (currentGame === "rpg") return `<div id="rpg-root"></div>`;
    if (currentGame === "2048") return window.GAMES_2048 ? window.GAMES_2048.renderHTML() : "";
    if (currentGame === "tictactoe") return window.GAMES_TICTACTOE ? window.GAMES_TICTACTOE.renderHTML() : "";
    if (currentGame === "snake") return window.GAMES_SNAKE ? window.GAMES_SNAKE.renderHTML() : "";
    if (currentGame === "tetris") return window.GAMES_TETRIS ? window.GAMES_TETRIS.renderHTML() : "";
    if (currentGame === "chess") return window.GAMES_CHESS ? window.GAMES_CHESS.renderHTML() : "";
    if (currentGame === "durak") return renderDurakHTML();
    return "";
  }


  // DURAK bridge
  function renderDurakHTML() {
    return `<div id="durak-root" style="min-height:400px;"></div>`;
  }

  function initDurak() {
    const el = document.getElementById('durak-root');
    if (!el) return;
    if (typeof window.DURAK !== 'undefined') {
      window.DURAK.init(el);
      return;
    }
    const scripts = [
      '/static/js/durak/durak_cards.js?v=20260911_2',
      '/static/js/durak/durak_menu.js?v=20260911_2',
      '/static/js/durak/durak_game.js?v=20260911_2',
      '/static/js/durak.js?v=20260911_2'
    ];
    let idx = 0;
    function loadNext() {
      if (idx >= scripts.length) {
        if (window.DURAK) window.DURAK.init(el);
        return;
      }
      const s = document.createElement('script');
      s.src = scripts[idx++];
      s.onload = loadNext;
      document.head.appendChild(s);
    }
    loadNext();
  }

  async function openOnlineRoom(roomId, gameType) {
    if (!roomId) return;
    let target = (gameType || "").toLowerCase().trim();

    if (!target) {
      try {
        if (window.api && typeof window.api.getGameRoom === "function") {
          const room = await window.api.getGameRoom(roomId);
          if (room && room.game_type) target = room.game_type;
        }
      } catch (e) {}
      if (!target) {
        try {
          const dRes = await fetch(`/api/durak/state/${roomId}`);
          if (dRes.ok) target = "durak";
        } catch (e) {}
      }
      if (!target) target = "tictactoe";
    }

    if (target === "rpg_duel") {
      switchGame("rpg");
      if (window.RPG && typeof window.RPG.openPvPRoom === "function") {
        window.RPG.openPvPRoom(roomId);
      }
      return;
    }
    if (target === "rpg_coop") {
      switchGame("rpg");
      if (window.RPG && typeof window.RPG.openCoopRoom === "function") {
        window.RPG.openCoopRoom(roomId);
      }
      return;
    }
    if (target === "chess") {
      switchGame("chess");
      if (window.GAMES_CHESS && typeof window.GAMES_CHESS.openChessOnlineRoom === "function") {
        return window.GAMES_CHESS.openChessOnlineRoom(roomId);
      }
      return;
    }
    if (target === "durak") {
      switchGame("durak");
      if (window.DURAK && typeof window.DURAK.joinRoom === "function") {
        return window.DURAK.joinRoom(roomId);
      }
      return;
    }
    switchGame("tictactoe");
    if (window.GAMES_TICTACTOE && typeof window.GAMES_TICTACTOE.openOnlineRoom === "function") {
      return window.GAMES_TICTACTOE.openOnlineRoom(roomId);
    }
  }

  // ПУБЛИЧНЫЙ ФАСАД window.GAMES (100% совместимость со всеми onclick в HTML)
  window.GAMES = {
    init: initGames,
    switchGame: switchGame,
    render: renderGames,
    getCurrentGame: () => currentGame,
    updateTesterStatus: updateTesterStatus,
    checkTesterStatus: checkTesterStatus,
    cleanup: cleanupCurrentGame,

    // natarGRP RPG
    initRPG: () => window.RPG && typeof window.RPG.init === "function" && window.RPG.init(),

    // 2048
    reset2048: () => window.GAMES_2048 && window.GAMES_2048.reset(),

    // Tic-Tac-Toe
    setTTTMode: (m) => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.setTTTMode(m),
    cellClickTTT: (i) => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.cellClickTTT(i),
    resetTTT: () => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.resetTTT(),
    openOnlineRoom: openOnlineRoom,
    inviteClassmate: (id, n) => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.inviteClassmate(id, n),
    makeOnlineMove: (i) => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.makeOnlineMove(i),
    requestRematch: () => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.requestRematch(),
    cancelOnlineGame: () => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.cancelOnlineGame(),
    leaveOnlineGame: () => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.leaveOnlineGame(),
    backToLobby: () => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.backToLobby(),
    filterClassmates: (q) => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.filterClassmates(q),
    refreshClassmates: () => window.GAMES_TICTACTOE && window.GAMES_TICTACTOE.loadClassmates(),

    // Snake
    startSnakeGame: () => window.GAMES_SNAKE && window.GAMES_SNAKE.startSnakeGame(),
    setSnakeDir: (d) => window.GAMES_SNAKE && window.GAMES_SNAKE.setSnakeDir(d),

    // Tetris
    startTetrisGame: () => window.GAMES_TETRIS && window.GAMES_TETRIS.startTetrisGame(),
    toggleTetrisPause: () => window.GAMES_TETRIS && window.GAMES_TETRIS.toggleTetrisPause(),
    tetrisMoveLeft: () => window.GAMES_TETRIS && window.GAMES_TETRIS.tetrisMoveLeft(),
    tetrisMoveRight: () => window.GAMES_TETRIS && window.GAMES_TETRIS.tetrisMoveRight(),
    tetrisRotate: () => window.GAMES_TETRIS && window.GAMES_TETRIS.tetrisRotate(),
    tetrisSoftDrop: () => window.GAMES_TETRIS && window.GAMES_TETRIS.tetrisSoftDrop(),
    tetrisHardDrop: () => window.GAMES_TETRIS && window.GAMES_TETRIS.tetrisHardDrop(),

    // Chess (Online & Local 2-Player)
    startLocalChessGame: () => window.GAMES_CHESS && window.GAMES_CHESS.startLocalChessGame(),
    toggleChessAutoRotate: () => window.GAMES_CHESS && window.GAMES_CHESS.toggleChessAutoRotate(),
    flipChessBoardManual: () => window.GAMES_CHESS && window.GAMES_CHESS.flipChessBoardManual(),
    openChessOnlineRoom: (c) => window.GAMES_CHESS && window.GAMES_CHESS.openChessOnlineRoom(c),
    inviteChessClassmate: (id, n) => window.GAMES_CHESS && window.GAMES_CHESS.inviteChessClassmate(id, n),
    chessSquareClick: (r, c) => window.GAMES_CHESS && window.GAMES_CHESS.chessSquareClick(r, c),
    choosePromotion: (p) => window.GAMES_CHESS && window.GAMES_CHESS.choosePromotion(p),
    resignChessGame: () => window.GAMES_CHESS && window.GAMES_CHESS.resignChessGame(),
    requestChessRematch: () => window.GAMES_CHESS && window.GAMES_CHESS.requestChessRematch(),
    cancelChessGame: () => window.GAMES_CHESS && window.GAMES_CHESS.cancelChessGame(),
    leaveChessGame: () => window.GAMES_CHESS && window.GAMES_CHESS.leaveChessGame(),
    backToChessLobby: () => window.GAMES_CHESS && window.GAMES_CHESS.backToChessLobby(),
    filterChessClassmates: (q) => window.GAMES_CHESS && window.GAMES_CHESS.filterChessClassmates(q),
    refreshChessClassmates: () => window.GAMES_CHESS && window.GAMES_CHESS.loadChessClassmates(),
    setChessColor: (c) => window.GAMES_CHESS && window.GAMES_CHESS.setChessColor(c)
  };
})();
