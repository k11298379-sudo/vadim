// ==============================================================================
// МОДУЛЬ МИНИ-ИГР ДЛЯ MINI APP (2048, КРЕСТИКИ-НОЛИКИ, ЗМЕЙКА)
// ==============================================================================

(function () {
  let currentGame = "2048"; // '2048', 'tictactoe', 'snake'

  function initGames() {
    const container = document.getElementById("pane-games");
    if (!container) return;
    renderGames();
  }

  function renderGames() {
    const container = document.getElementById("pane-games");
    if (!container) return;

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
          <span class="text-[11px] font-bold px-2 py-0.5 rounded-lg bg-violet-50 dark:bg-slate-800 text-violet-600 dark:text-violet-400 border border-violet-100 dark:border-slate-700">4 игры</span>
        </div>

        <!-- Games selector tabs -->
        <div class="grid grid-cols-4 gap-1 p-1 rounded-2xl bg-slate-200/70 dark:bg-slate-800/90 text-[11px] font-bold">
          <button onclick="window.GAMES.switchGame('2048')" class="py-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
            currentGame === '2048'
              ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'
          }">
            <span>🔢</span>
            <span class="truncate">2048</span>
          </button>
          <button onclick="window.GAMES.switchGame('tictactoe')" class="py-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
            currentGame === 'tictactoe'
              ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'
          }">
            <span>❌⭕</span>
            <span class="truncate">Крестики</span>
          </button>
          <button onclick="window.GAMES.switchGame('snake')" class="py-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
            currentGame === 'snake'
              ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'
          }">
            <span>🐍</span>
            <span class="truncate">Змейка</span>
          </button>
          <button onclick="window.GAMES.switchGame('chess')" class="py-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
            currentGame === 'chess'
              ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'
          }">
            <span>♟️</span>
            <span class="truncate">Шахматы</span>
          </button>
        </div>
      </div>

      <!-- Game Canvas / Container -->
      <div id="game-active-container" class="pt-1">
        ${renderActiveGame()}
      </div>
    `;

    // After DOM update, initialize specific game listeners
    if (currentGame === "2048") init2048();
    else if (currentGame === "tictactoe") initTicTacToe();
    else if (currentGame === "snake") initSnake();
    else if (currentGame === "chess") initChess();
  }

  function switchGame(gameId) {
    cleanupCurrentGame();
    currentGame = gameId;
    renderGames();
  }

  function cleanupCurrentGame() {
    stopOnlinePolling();
    stopChessPolling();
    if (window._snakeInterval) {
      clearInterval(window._snakeInterval);
      window._snakeInterval = null;
    }
  }

  function renderActiveGame() {
    if (currentGame === "2048") return render2048HTML();
    if (currentGame === "tictactoe") return renderTicTacToeHTML();
    if (currentGame === "snake") return renderSnakeHTML();
    if (currentGame === "chess") return renderChessHTML();
    return "";
  }

  // ==============================================================================
  // GAME 1: 2048
  // ==============================================================================
  let board2048 = [];
  let score2048 = 0;
  let best2048 = 0;

  function render2048HTML() {
    best2048 = parseInt(localStorage.getItem("game_2048_best") || "0", 10);
    return `
      <div class="theme-card rounded-3xl p-4 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-4 max-w-sm mx-auto">
        <!-- Top bar: Score & New Game -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-700 text-center">
              <span class="block text-[9px] font-bold text-slate-400 uppercase">Счёт</span>
              <span id="score-2048" class="text-sm font-black text-slate-800 dark:text-white">0</span>
            </div>
            <div class="px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-center border border-amber-200/60 dark:border-amber-800/40">
              <span class="block text-[9px] font-bold text-amber-500 uppercase">Рекорд</span>
              <span id="best-2048" class="text-sm font-black text-amber-600 dark:text-amber-400">${best2048}</span>
            </div>
          </div>
          <button onclick="window.GAMES.reset2048()" class="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1">
            <span>🔄</span> Заново
          </button>
        </div>

        <!-- 4x4 Grid Container -->
        <div id="grid-2048" class="w-full aspect-square p-2 rounded-2xl bg-slate-200 dark:bg-slate-900 grid grid-cols-4 gap-2 touch-none select-none">
          <!-- 16 cells generated in init2048 -->
        </div>

        <!-- Hint / Touch controls -->
        <div class="text-center text-[11px] text-slate-400">
          Свайпайте в любую сторону для объединения одинаковых плиток
        </div>
      </div>
    `;
  }

  function init2048() {
    board2048 = [
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0]
    ];
    score2048 = 0;
    addRandomTile2048();
    addRandomTile2048();
    updateBoard2048DOM();
    setupSwipe2048();
  }

  function addRandomTile2048() {
    const empty = [];
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 4; c++) {
        if (board2048[r][c] === 0) empty.push({ r, c });
      }
    }
    if (empty.length === 0) return;
    const { r, c } = empty[Math.floor(Math.random() * empty.length)];
    board2048[r][c] = Math.random() < 0.9 ? 2 : 4;
  }

  function getTileColor(val) {
    const map = {
      2: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xl font-bold",
      4: "bg-amber-100 dark:bg-amber-900/60 text-amber-900 dark:text-amber-100 text-xl font-bold",
      8: "bg-orange-400 text-white text-xl font-extrabold",
      16: "bg-orange-500 text-white text-xl font-extrabold",
      32: "bg-red-500 text-white text-xl font-extrabold",
      64: "bg-red-600 text-white text-xl font-extrabold",
      128: "bg-yellow-400 text-slate-900 text-lg font-black shadow-md",
      256: "bg-yellow-500 text-slate-900 text-lg font-black shadow-md",
      512: "bg-yellow-600 text-white text-lg font-black shadow-md",
      1024: "bg-emerald-500 text-white text-base font-black shadow-lg",
      2048: "bg-gradient-to-tr from-amber-400 to-yellow-300 text-slate-900 text-base font-black shadow-xl ring-2 ring-yellow-400"
    };
    return map[val] || "bg-indigo-600 text-white text-sm font-black";
  }

  function updateBoard2048DOM() {
    const gridEl = document.getElementById("grid-2048");
    if (!gridEl) return;

    let html = "";
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 4; c++) {
        const val = board2048[r][c];
        if (val === 0) {
          html += `<div class="rounded-xl bg-slate-300/40 dark:bg-slate-800/40"></div>`;
        } else {
          html += `
            <div class="rounded-xl flex items-center justify-center transition-all ${getTileColor(val)}">
              ${val}
            </div>
          `;
        }
      }
    }
    gridEl.innerHTML = html;

    const scoreEl = document.getElementById("score-2048");
    if (scoreEl) scoreEl.textContent = score2048;

    if (score2048 > best2048) {
      best2048 = score2048;
      localStorage.setItem("game_2048_best", best2048);
      const bestEl = document.getElementById("best-2048");
      if (bestEl) bestEl.textContent = best2048;
    }
  }

  function move2048(direction) {
    let moved = false;

    function slide(row) {
      let arr = row.filter(val => val !== 0);
      for (let i = 0; i < arr.length - 1; i++) {
        if (arr[i] === arr[i + 1]) {
          arr[i] *= 2;
          score2048 += arr[i];
          arr[i + 1] = 0;
          moved = true;
        }
      }
      arr = arr.filter(val => val !== 0);
      while (arr.length < 4) arr.push(0);
      return arr;
    }

    const prevBoard = JSON.stringify(board2048);

    if (direction === "left") {
      for (let r = 0; r < 4; r++) board2048[r] = slide(board2048[r]);
    } else if (direction === "right") {
      for (let r = 0; r < 4; r++) {
        board2048[r].reverse();
        board2048[r] = slide(board2048[r]);
        board2048[r].reverse();
      }
    } else if (direction === "up") {
      for (let c = 0; c < 4; c++) {
        let col = [board2048[0][c], board2048[1][c], board2048[2][c], board2048[3][c]];
        col = slide(col);
        for (let r = 0; r < 4; r++) board2048[r][c] = col[r];
      }
    } else if (direction === "down") {
      for (let c = 0; c < 4; c++) {
        let col = [board2048[0][c], board2048[1][c], board2048[2][c], board2048[3][c]];
        col.reverse();
        col = slide(col);
        col.reverse();
        for (let r = 0; r < 4; r++) board2048[r][c] = col[r];
      }
    }

    if (JSON.stringify(board2048) !== prevBoard) {
      addRandomTile2048();
      updateBoard2048DOM();
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
      }
    }
  }

  function setupSwipe2048() {
    const gridEl = document.getElementById("grid-2048");
    if (!gridEl) return;

    let startX = 0;
    let startY = 0;

    gridEl.addEventListener("touchstart", (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }, { passive: true });

    gridEl.addEventListener("touchend", (e) => {
      const diffX = e.changedTouches[0].clientX - startX;
      const diffY = e.changedTouches[0].clientY - startY;
      const absX = Math.abs(diffX);
      const absY = Math.abs(diffY);

      if (Math.max(absX, absY) > 25) {
        if (absX > absY) {
          move2048(diffX > 0 ? "right" : "left");
        } else {
          move2048(diffY > 0 ? "down" : "up");
        }
      }
    }, { passive: true });
  }

  // ==============================================================================
  // GAME 2: TIC-TAC-TOE (Крестики-нолики с поддержкой Онлайн-дуэли через бота)
  // ==============================================================================
  let tttBoard = ["", "", "", "", "", "", "", "", ""];
  let tttTurn = "X";
  let tttMode = "bot"; // 'bot', 'local', 'online'
  let tttScore = { X: 0, O: 0, draw: 0 };
  let tttGameOver = false;

  // Online Duel State
  let onlineState = "lobby"; // 'lobby', 'loading', 'waiting', 'playing', 'finished', 'rejected'
  let onlineRoomId = null;
  let onlineRoomData = null;
  let onlineOpponentName = "";
  let onlinePollTimer = null;
  let isOnlinePolling = false;
  let classmatesList = [];
  let classmatesFilter = "";
  let isLoadingClassmates = false;

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderTicTacToeHTML() {
    return `
      <div class="theme-card rounded-3xl p-4 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-3.5 max-w-sm mx-auto text-center">
        <!-- Game Mode Selector -->
        <div class="grid grid-cols-3 gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-700/80 text-[11px] font-bold">
          <button onclick="window.GAMES.setTTTMode('bot')" class="py-1.5 px-2 rounded-lg transition-all flex items-center justify-center gap-1 ${tttMode === 'bot' ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-500 dark:text-slate-400'}">
            <span>🤖</span><span>С ботом</span>
          </button>
          <button onclick="window.GAMES.setTTTMode('local')" class="py-1.5 px-2 rounded-lg transition-all flex items-center justify-center gap-1 ${tttMode === 'local' ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-500 dark:text-slate-400'}">
            <span>👥</span><span>На двоих</span>
          </button>
          <button onclick="window.GAMES.setTTTMode('online')" class="py-1.5 px-2 rounded-lg transition-all flex items-center justify-center gap-1 ${tttMode === 'online' ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-500 dark:text-slate-400'}">
            <span>🌐</span><span>Онлайн дуэль</span>
          </button>
        </div>

        ${tttMode === 'online' ? renderOnlineTTTHTML() : renderLocalTTTHTML()}
      </div>
    `;
  }

  function renderLocalTTTHTML() {
    return `
      <!-- Turn indicator & Reset -->
      <div class="flex items-center justify-between px-1">
        <div id="ttt-status" class="text-xs font-bold text-slate-500">
          Ход: <span class="text-blue-600 dark:text-blue-400 text-sm font-black">${tttTurn}</span>
        </div>
        <button onclick="window.GAMES.resetTTT()" class="p-1.5 px-2.5 rounded-xl bg-slate-100 dark:bg-slate-700 text-xs font-bold text-slate-500 hover:text-slate-800 dark:hover:text-white flex items-center gap-1 transition-all active:scale-95">
          <span>🔄</span> Заново
        </button>
      </div>

      <!-- 3x3 Board -->
      <div class="grid grid-cols-3 gap-2 w-64 h-64 mx-auto p-2 rounded-2xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 select-none">
        ${[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => `
          <button
            id="ttt-cell-${i}"
            onclick="window.GAMES.cellClickTTT(${i})"
            class="w-full h-full rounded-xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-3xl font-black flex items-center justify-center transition-all hover:bg-blue-50/50 active:scale-95 shadow-sm">
          </button>
        `).join('')}
      </div>

      <!-- Scoreboard -->
      <div class="flex items-center justify-center gap-4 text-xs font-bold pt-1">
        <span class="text-blue-600">Крестики (X): <b id="ttt-score-x">${tttScore.X}</b></span>
        <span class="text-slate-400">Ничьи: <b id="ttt-score-d">${tttScore.draw}</b></span>
        <span class="text-rose-500">Нолики (O): <b id="ttt-score-o">${tttScore.O}</b></span>
      </div>
    `;
  }

  function renderOnlineTTTHTML() {
    if (onlineState === "loading") {
      return `
        <div class="py-12 space-y-3">
          <div class="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p class="text-xs font-bold text-slate-500">Подключение к игре...</p>
        </div>
      `;
    }

    if (onlineState === "waiting") {
      const oppName = onlineOpponentName || (onlineRoomData?.opponent?.name) || "Одноклассник";
      return `
        <div class="py-8 space-y-4">
          <div class="w-16 h-16 rounded-3xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center text-3xl mx-auto shadow-inner animate-pulse">
            ⏳
          </div>
          <div class="space-y-1">
            <h3 class="text-sm font-black text-slate-800 dark:text-white">Вызов отправлен: ${escapeHtml(oppName)}</h3>
            <p class="text-[11px] text-slate-400 max-w-xs mx-auto">
              Бот отправил однокласснику приглашение с кнопкой входа. Ждем подключения...
            </p>
          </div>
          <button
            onclick="window.GAMES.cancelOnlineGame()"
            class="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 font-bold text-xs transition-all active:scale-95">
            ❌ Отменить вызов
          </button>
        </div>
      `;
    }

    if (onlineState === "rejected") {
      return `
        <div class="py-8 space-y-3">
          <div class="text-4xl">❌</div>
          <h3 class="text-sm font-black text-slate-800 dark:text-white">Вызов отклонен или отменен</h3>
          <p class="text-xs text-slate-400">Соперник отклонил приглашение или вызов был отменен.</p>
          <button
            onclick="window.GAMES.backToLobby()"
            class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition-all active:scale-95">
            🔙 Вернуться к списку
          </button>
        </div>
      `;
    }

    if (onlineState === "playing" || onlineState === "finished") {
      const hostName = onlineRoomData?.host?.name || "Хост";
      const oppName = onlineRoomData?.opponent?.name || "Соперник";
      const yourRole = onlineRoomData?.your_role;
      const isYourTurn = onlineRoomData?.is_your_turn;
      const isFinished = onlineState === "finished";

      let statusHTML = "";
      if (isFinished) {
        if (onlineRoomData.winner === "draw") {
          statusHTML = `<div class="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-extrabold">🤝 Боевая ничья!</div>`;
        } else if (onlineRoomData.winner === yourRole) {
          statusHTML = `<div class="p-2.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-extrabold animate-pulse">🎉 Победа! Ты выиграл дуэль!</div>`;
        } else {
          const winnerName = onlineRoomData.winner === "X" ? hostName : oppName;
          statusHTML = `<div class="p-2.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-extrabold">😔 Победил ${escapeHtml(winnerName)}</div>`;
        }
      } else {
        if (isYourTurn) {
          statusHTML = `<div class="p-2.5 rounded-2xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400 text-xs font-extrabold animate-pulse">👉 Твой ход! Поставь ${yourRole}</div>`;
        } else {
          const waitingFor = onlineRoomData?.turn === "X" ? hostName : oppName;
          statusHTML = `<div class="p-2.5 rounded-2xl bg-slate-100 dark:bg-slate-700/60 text-slate-500 dark:text-slate-400 text-xs font-bold">⏳ Ход соперника (${escapeHtml(waitingFor)})...</div>`;
        }
      }

      return `
        <!-- Matchup Header -->
        <div class="flex items-center justify-between p-2 rounded-2xl bg-slate-100 dark:bg-slate-700/60 text-xs font-bold">
          <div class="flex items-center gap-1.5 min-w-0 pr-1 ${yourRole === 'X' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-200'}">
            <span class="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300 flex items-center justify-center font-black text-[11px] shrink-0">X</span>
            <span class="truncate max-w-[85px]">${escapeHtml(hostName)}${yourRole === 'X' ? ' (Вы)' : ''}</span>
          </div>
          <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest shrink-0">VS</span>
          <div class="flex items-center gap-1.5 min-w-0 pl-1 ${yourRole === 'O' ? 'text-rose-600 dark:text-rose-400' : 'text-slate-700 dark:text-slate-200'}">
            <span class="truncate max-w-[85px]">${escapeHtml(oppName)}${yourRole === 'O' ? ' (Вы)' : ''}</span>
            <span class="w-5 h-5 rounded-full bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-300 flex items-center justify-center font-black text-[11px] shrink-0">O</span>
          </div>
        </div>

        <!-- Status / Turn Banner -->
        ${statusHTML}

        <!-- 3x3 Board -->
        <div class="grid grid-cols-3 gap-2 w-64 h-64 mx-auto p-2 rounded-2xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 select-none">
          ${[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => {
            const val = onlineRoomData?.board?.[i] || "";
            const canClick = !isFinished && isYourTurn && val === "";
            return `
              <button
                id="online-cell-${i}"
                ${canClick ? `onclick="window.GAMES.makeOnlineMove(${i})"` : 'disabled'}
                class="w-full h-full rounded-xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-3xl font-black flex items-center justify-center transition-all ${
                  val === 'X' ? 'text-blue-600' : val === 'O' ? 'text-rose-500' : ''
                } ${canClick ? 'hover:bg-blue-50/50 dark:hover:bg-slate-700 active:scale-95 cursor-pointer shadow-sm' : 'cursor-default'}" style="touch-action: manipulation;">
                ${val}
              </button>
            `;
          }).join('')}
        </div>

        <!-- Action Buttons -->
        <div class="space-y-2 pt-1">
          ${isFinished ? `
            ${onlineRoomData?.rematch_requested_by ? `
              ${onlineRoomData.rematch_requested_by === yourRole ? `
                <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-700 text-xs font-bold text-slate-500 flex items-center justify-center gap-1.5">
                  <span class="animate-spin">⏳</span> Ждем согласие соперника на реванш...
                </div>
              ` : `
                <button
                  onclick="window.GAMES.requestRematch()"
                  class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black text-xs shadow-md transition-all flex items-center justify-center gap-1.5">
                  <span>🔥</span> Соперник ждет реванш! Принять бой
                </button>
              `}
            ` : `
              <button
                onclick="window.GAMES.requestRematch()"
                class="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-black text-xs shadow-md transition-all flex items-center justify-center gap-1.5">
                <span>🔄</span> Предложить реванш
              </button>
            `}
            <button
              onclick="window.GAMES.leaveOnlineGame()"
              class="w-full py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 text-slate-500 font-bold text-xs transition-all active:scale-95">
              🚪 Выйти в лобби
            </button>
          ` : `
            <button
              onclick="window.GAMES.leaveOnlineGame()"
              class="text-xs text-slate-400 hover:text-rose-500 font-medium transition-all">
              Сдаться и выйти
            </button>
          `}
        </div>
      `;
    }

    // Default: Lobby
    return `
      <div class="space-y-3">
        <div class="text-left px-1 space-y-0.5">
          <h3 class="text-xs font-black text-slate-800 dark:text-white flex items-center gap-1">
            <span>⚔️</span> Вызов одноклассника
          </h3>
          <p class="text-[11px] text-slate-400">
            Бот мгновенно пришлет однокласснику в Telegram кнопку входа в игру
          </p>
        </div>

        <!-- Search & Refresh -->
        <div class="flex items-center gap-1.5">
          <input
            type="text"
            id="classmate-filter-input"
            value="${escapeHtml(classmatesFilter)}"
            oninput="window.GAMES.filterClassmates(this.value)"
            placeholder="🔍 Поиск одноклассника..."
            class="flex-1 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
          <button
            onclick="window.GAMES.refreshClassmates()"
            title="Обновить"
            class="p-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-500 hover:text-slate-800 dark:hover:text-white transition-all active:scale-95">
            🔄
          </button>
        </div>

        <!-- Classmates List Container -->
        <div id="classmates-wrapper">
          ${isLoadingClassmates ? `
            <div class="py-8 text-center text-xs text-slate-400 space-y-2">
              <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <span>Загрузка одноклассников...</span>
            </div>
          ` : renderClassmateList()}
        </div>
      </div>
    `;
  }

  function renderClassmateList() {
    const q = (classmatesFilter || "").toLowerCase().trim();
    const filtered = classmatesList.filter(c => {
      const name = (c.name || c.full_name || "").toLowerCase();
      return !q || name.includes(q);
    });

    if (filtered.length === 0) {
      return `
        <div class="py-8 text-center text-xs text-slate-400">
          ${q ? "Никого не найдено по запросу" : "Одноклассники не найдены"}
        </div>
      `;
    }

    return `
      <div id="classmates-container" class="space-y-1.5 max-h-56 overflow-y-auto pr-1">
        ${filtered.map(c => {
          const name = c.name || c.full_name || "Одноклассник";
          const initial = name.charAt(0).toUpperCase();
          return `
            <div class="flex items-center justify-between p-2 rounded-2xl bg-slate-50 dark:bg-slate-700/50 border border-slate-200/60 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-500/50 transition-all">
              <div class="flex items-center gap-2 min-w-0 pr-2">
                <div class="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300 font-black text-xs flex items-center justify-center shrink-0">
                  ${initial}
                </div>
                <div class="truncate text-left">
                  <div class="text-xs font-bold text-slate-800 dark:text-white truncate">${escapeHtml(name)}</div>
                  <div class="text-[10px] text-slate-400">11 «Б»</div>
                </div>
              </div>
              <button
                onclick="window.GAMES.inviteClassmate(${c.tg_id}, '${escapeHtml(name)}')"
                class="shrink-0 px-3 py-1.5 rounded-xl font-black text-xs bg-blue-600 hover:bg-blue-700 active:scale-95 text-white shadow-sm transition-all flex items-center gap-1">
                <span>⚔️</span> Вызвать
              </button>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function initTicTacToe() {
    tttBoard = ["", "", "", "", "", "", "", "", ""];
    tttTurn = "X";
    tttGameOver = false;
    updateTTTDOM();
  }

  function setTTTMode(mode) {
    stopOnlinePolling();
    if (typeof mode === "boolean") {
      mode = mode ? "bot" : "local";
    }
    tttMode = mode;
    if (mode === "online") {
      onlineState = "lobby";
      loadClassmates();
    } else {
      tttScore = { X: 0, O: 0, draw: 0 };
      initTicTacToe();
    }
    renderGames();
  }

  function resetTTT() {
    if (tttMode === "online") {
      if (onlineState === "playing" || onlineState === "finished") {
        requestRematch();
      } else {
        loadClassmates();
      }
    } else {
      initTicTacToe();
    }
  }

  function cellClickTTT(idx) {
    if (tttGameOver || tttBoard[idx] !== "") return;

    makeMoveTTT(idx, tttTurn);

    if (!tttGameOver && tttMode === "bot" && tttTurn === "O") {
      setTimeout(() => {
        botMoveTTT();
      }, 300);
    }
  }

  function makeMoveTTT(idx, player) {
    tttBoard[idx] = player;
    updateTTTDOM();

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
    }

    const winner = checkWinnerTTT();
    if (winner) {
      tttGameOver = true;
      const statusEl = document.getElementById("ttt-status");
      if (winner === "draw") {
        tttScore.draw++;
        if (statusEl) statusEl.innerHTML = `<span class="text-amber-500 font-extrabold text-sm">🤝 Ничья!</span>`;
      } else {
        tttScore[winner]++;
        if (statusEl) statusEl.innerHTML = `<span class="text-emerald-500 font-extrabold text-sm">🎉 Победил ${winner}!</span>`;
        if (window.Telegram?.WebApp?.HapticFeedback) {
          window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
        }
      }
      updateScoreTTT();
      return;
    }

    tttTurn = tttTurn === "X" ? "O" : "X";
    const statusEl = document.getElementById("ttt-status");
    if (statusEl) statusEl.innerHTML = `Ход: <span class="text-blue-600 dark:text-blue-400 text-sm font-black">${tttTurn}</span>`;
  }

  function botMoveTTT() {
    if (tttGameOver) return;

    // 1. Can bot win in 1 move?
    for (let i = 0; i < 9; i++) {
      if (tttBoard[i] === "") {
        tttBoard[i] = "O";
        if (checkWinnerTTT() === "O") {
          tttBoard[i] = "";
          makeMoveTTT(i, "O");
          return;
        }
        tttBoard[i] = "";
      }
    }

    // 2. Can player win in 1 move? Block them!
    for (let i = 0; i < 9; i++) {
      if (tttBoard[i] === "") {
        tttBoard[i] = "X";
        if (checkWinnerTTT() === "X") {
          tttBoard[i] = "";
          makeMoveTTT(i, "O");
          return;
        }
        tttBoard[i] = "";
      }
    }

    // 3. Take center if available
    if (tttBoard[4] === "") {
      makeMoveTTT(4, "O");
      return;
    }

    // 4. Random empty cell
    const empty = [];
    for (let i = 0; i < 9; i++) {
      if (tttBoard[i] === "") empty.push(i);
    }
    if (empty.length > 0) {
      const chosen = empty[Math.floor(Math.random() * empty.length)];
      makeMoveTTT(chosen, "O");
    }
  }

  function checkWinnerTTT() {
    const lines = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
      [0, 3, 6], [1, 4, 7], [2, 5, 8], // Cols
      [0, 4, 8], [2, 4, 6]             // Diagonals
    ];
    for (let [a, b, c] of lines) {
      if (tttBoard[a] && tttBoard[a] === tttBoard[b] && tttBoard[a] === tttBoard[c]) {
        return tttBoard[a];
      }
    }
    if (tttBoard.every(cell => cell !== "")) return "draw";
    return null;
  }

  function updateTTTDOM() {
    for (let i = 0; i < 9; i++) {
      const cell = document.getElementById(`ttt-cell-${i}`);
      if (cell) {
        cell.textContent = tttBoard[i];
        cell.className = `w-full h-full rounded-xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-3xl font-black flex items-center justify-center transition-all ${
          tttBoard[i] === "X" ? "text-blue-600" : tttBoard[i] === "O" ? "text-rose-500" : ""
        }`;
      }
    }
  }

  function updateScoreTTT() {
    const xEl = document.getElementById("ttt-score-x");
    const oEl = document.getElementById("ttt-score-o");
    const dEl = document.getElementById("ttt-score-d");
    if (xEl) xEl.textContent = tttScore.X;
    if (oEl) oEl.textContent = tttScore.O;
    if (dEl) dEl.textContent = tttScore.draw;
  }

  // --- ONLINE MULTIPLAYER LOGIC ---

  async function loadClassmates() {
    isLoadingClassmates = true;
    renderGames();
    try {
      classmatesList = await api.getClassmates();
    } catch (e) {
      console.warn("Could not load classmates:", e);
      classmatesList = [];
    } finally {
      isLoadingClassmates = false;
      renderGames();
    }
  }

  function filterClassmates(val) {
    classmatesFilter = val;
    const wrapper = document.getElementById("classmates-wrapper");
    if (wrapper) {
      wrapper.innerHTML = renderClassmateList();
    }
  }

  async function inviteClassmate(tgId, oppName) {
    onlineOpponentName = oppName;
    onlineState = "waiting";
    renderGames();

    try {
      let myName = "Одноклассник";
      try {
        const me = await api.getMe();
        if (me && me.full_name) myName = me.full_name;
      } catch (e) {}

      const res = await api.inviteGame(tgId, myName, "tictactoe", "white", oppName);
      onlineRoomId = res.room_id;
      onlineRoomData = res;
      startOnlinePolling();
    } catch (e) {
      alert("Не удалось отправить вызов: " + (e.message || "Ошибка"));
      onlineState = "lobby";
      renderGames();
    }
  }

  async function openTTTOnlineRoom(roomId) {
    currentGame = "tictactoe";
    tttMode = "online";
    onlineRoomId = roomId;
    onlineState = "loading";
    renderGames();

    try {
      let myName = "Игрок";
      try {
        const me = await api.getMe();
        if (me && me.full_name) myName = me.full_name;
      } catch (e) {}

      const room = await api.joinGameRoom(roomId, myName);
      onlineRoomData = room;
      if (room.status === "finished") {
        onlineState = "finished";
      } else if (room.status === "waiting") {
        onlineState = "waiting";
      } else {
        onlineState = "playing";
      }
      renderGames();
      startOnlinePolling();
    } catch (e) {
      console.error("Failed to join online room:", e);
      onlineState = "rejected";
      renderGames();
    }
  }

  async function openOnlineRoom(roomId, gameType) {
    if (gameType === "chess") {
      return openChessOnlineRoom(roomId);
    }
    try {
      const room = await api.getGameRoom(roomId);
      if (room && room.game_type === "chess") {
        return openChessOnlineRoom(roomId);
      }
    } catch (e) {}
    return openTTTOnlineRoom(roomId);
  }

  async function makeOnlineMove(cellIdx) {
    if (!onlineRoomId || !onlineRoomData || !onlineRoomData.is_your_turn) return;
    if (onlineRoomData.board[cellIdx] !== "") return;

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
    }

    try {
      const updated = await api.sendGameMove(onlineRoomId, cellIdx);
      handleRoomUpdate(updated);
    } catch (e) {
      console.warn("Move error:", e);
    }
  }

  async function requestRematch() {
    if (!onlineRoomId) return;
    try {
      const updated = await api.rematchGame(onlineRoomId);
      handleRoomUpdate(updated);
      renderGames();
    } catch (e) {
      alert("Ошибка реванша: " + (e.message || "Ошибка"));
    }
  }

  async function cancelOnlineGame() {
    if (onlineRoomId) {
      try {
        await api.cancelGame(onlineRoomId);
      } catch (e) {}
    }
    stopOnlinePolling();
    onlineRoomId = null;
    onlineRoomData = null;
    onlineState = "lobby";
    renderGames();
  }

  function leaveOnlineGame() {
    stopOnlinePolling();
    onlineRoomId = null;
    onlineRoomData = null;
    onlineState = "lobby";
    renderGames();
  }

  function backToLobby() {
    stopOnlinePolling();
    onlineRoomId = null;
    onlineRoomData = null;
    onlineState = "lobby";
    loadClassmates();
  }

  function startOnlinePolling() {
    stopOnlinePolling();
    isOnlinePolling = true;
    pollRoomState();
  }

  function stopOnlinePolling() {
    isOnlinePolling = false;
    if (onlinePollTimer) {
      clearTimeout(onlinePollTimer);
      onlinePollTimer = null;
    }
  }

  async function pollRoomState() {
    if (!isOnlinePolling || !onlineRoomId) return;

    try {
      const data = await api.getGameRoom(onlineRoomId);
      handleRoomUpdate(data);
    } catch (e) {
      console.warn("Error polling online room:", e);
    }

    if (isOnlinePolling && onlineRoomId) {
      onlinePollTimer = setTimeout(pollRoomState, 800);
    }
  }

  function handleRoomUpdate(data) {
    if (!data) return;
    const oldStatus = onlineRoomData ? onlineRoomData.status : null;
    const oldTurn = onlineRoomData ? onlineRoomData.turn : null;
    const oldBoard = onlineRoomData ? JSON.stringify(onlineRoomData.board) : "";
    const oldRematch = onlineRoomData ? onlineRoomData.rematch_requested_by : null;

    onlineRoomData = data;

    if (data.status === "rejected" || data.status === "canceled") {
      stopOnlinePolling();
      onlineState = "rejected";
      renderGames();
      return;
    }

    if (data.status === "waiting") {
      if (onlineState !== "waiting") {
        onlineState = "waiting";
        renderGames();
      }
      return;
    }

    if (data.status === "playing") {
      if (onlineState !== "playing" || oldBoard !== JSON.stringify(data.board) || oldTurn !== data.turn) {
        onlineState = "playing";
        renderGames();
        if (window.Telegram?.WebApp?.HapticFeedback) {
          window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
        }
      }
      return;
    }

    if (data.status === "finished") {
      if (onlineState !== "finished") {
        onlineState = "finished";
        renderGames();
        if (window.Telegram?.WebApp?.HapticFeedback) {
          if (data.winner === data.your_role) {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
          } else if (data.winner === "draw") {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("warning");
          } else {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
          }
        }
      } else if (oldRematch !== data.rematch_requested_by) {
        renderGames();
      }
      return;
    }
  }

  // ==============================================================================
  // GAME 3: SNAKE (Змейка)
  // ==============================================================================
  let snake = [];
  let snakeFood = { x: 5, y: 5 };
  let snakeDir = { x: 1, y: 0 };
  let snakeScore = 0;
  let snakeBest = 0;
  let snakeRunning = false;

  function renderSnakeHTML() {
    snakeBest = parseInt(localStorage.getItem("game_snake_best") || "0", 10);
    return `
      <div class="theme-card rounded-3xl p-4 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-3 max-w-sm mx-auto text-center">
        <!-- Top bar -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="px-3 py-1 rounded-xl bg-slate-100 dark:bg-slate-700 text-center">
              <span class="block text-[9px] font-bold text-slate-400 uppercase">Яблок</span>
              <span id="snake-score" class="text-sm font-black text-slate-800 dark:text-white">0</span>
            </div>
            <div class="px-3 py-1 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-center border border-emerald-200/60 dark:border-emerald-800/40">
              <span class="block text-[9px] font-bold text-emerald-500 uppercase">Рекорд</span>
              <span id="snake-best" class="text-sm font-black text-emerald-600 dark:text-emerald-400">${snakeBest}</span>
            </div>
          </div>
          <button onclick="window.GAMES.startSnakeGame()" class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition-all">
            ▶️ Старт
          </button>
        </div>

        <!-- Canvas & Touch Zone -->
        <div id="snake-touch-zone" class="relative w-full aspect-square max-w-[290px] mx-auto rounded-2xl overflow-hidden bg-slate-900 border-2 border-slate-800 shadow-inner select-none cursor-pointer" style="touch-action: none;">
          <canvas id="snake-canvas" width="290" height="290" class="w-full h-full block"></canvas>
          <div id="snake-overlay" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white">
            <span class="text-3xl">🐍</span>
            <p class="text-xs font-bold">Нажмите «Старт» для игры</p>
          </div>
        </div>

        <!-- Gesture / Swipe Control Hint -->
        <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-700/40 border border-slate-200/70 dark:border-slate-700 text-center space-y-1">
          <div class="text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center gap-1.5">
            <span class="text-base">👆</span>
            <span>Управление жестами (свайпами)</span>
          </div>
          <p class="text-[11px] text-slate-400">
            Смахивайте пальцем по экрану в нужную сторону для поворота
          </p>
        </div>
      </div>
    `;
  }

  const GRID_SIZE = 14; // 14x14 cells (20px each)
  let snakeTouchStartX = 0;
  let snakeTouchStartY = 0;

  function setupSnakeTouchListeners() {
    const zone = document.getElementById("snake-touch-zone");
    if (!zone || zone._touchSetup) return;
    zone._touchSetup = true;

    zone.addEventListener("touchstart", (e) => {
      if (e.touches && e.touches.length > 0) {
        snakeTouchStartX = e.touches[0].clientX;
        snakeTouchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    zone.addEventListener("touchmove", (e) => {
      if (!snakeRunning || !e.touches || e.touches.length === 0) return;
      const curX = e.touches[0].clientX;
      const curY = e.touches[0].clientY;
      const diffX = curX - snakeTouchStartX;
      const diffY = curY - snakeTouchStartY;
      const threshold = 18;

      if (Math.max(Math.abs(diffX), Math.abs(diffY)) >= threshold) {
        if (Math.abs(diffX) > Math.abs(diffY)) {
          setSnakeDir(diffX > 0 ? 1 : -1, 0);
        } else {
          setSnakeDir(0, diffY > 0 ? 1 : -1);
        }
        snakeTouchStartX = curX;
        snakeTouchStartY = curY;
        if (window.Telegram?.WebApp?.HapticFeedback) {
          window.Telegram.WebApp.HapticFeedback.selectionChanged();
        }
      }
      e.preventDefault();
    }, { passive: false });

    if (!window._snakeKeySetup) {
      window._snakeKeySetup = true;
      window.addEventListener("keydown", (e) => {
        if (currentGame !== "snake" || !snakeRunning) return;
        if (e.key === "ArrowUp" || e.code === "KeyW") setSnakeDir(0, -1);
        else if (e.key === "ArrowDown" || e.code === "KeyS") setSnakeDir(0, 1);
        else if (e.key === "ArrowLeft" || e.code === "KeyA") setSnakeDir(-1, 0);
        else if (e.key === "ArrowRight" || e.code === "KeyD") setSnakeDir(1, 0);
      });
    }
  }

  function initSnake() {
    snake = [
      { x: 4, y: 7 },
      { x: 3, y: 7 },
      { x: 2, y: 7 }
    ];
    snakeDir = { x: 1, y: 0 };
    snakeScore = 0;
    snakeRunning = false;
    spawnFood();
    drawSnakeCanvas();
    setupSnakeTouchListeners();
  }

  function spawnFood() {
    snakeFood = {
      x: Math.floor(Math.random() * GRID_SIZE),
      y: Math.floor(Math.random() * GRID_SIZE)
    };
  }

  function startSnakeGame() {
    initSnake();
    snakeRunning = true;
    const overlay = document.getElementById("snake-overlay");
    if (overlay) overlay.classList.add("hidden");

    if (window._snakeInterval) clearInterval(window._snakeInterval);
    window._snakeInterval = setInterval(snakeTick, 140);
  }

  function setSnakeDir(dx, dy) {
    if (!snakeRunning) return;
    // Prevent 180-degree turn
    if (snakeDir.x + dx === 0 && snakeDir.y + dy === 0) return;
    snakeDir = { x: dx, y: dy };
  }

  function snakeTick() {
    if (!snakeRunning) return;

    const head = { x: snake[0].x + snakeDir.x, y: snake[0].y + snakeDir.y };

    // Wall collision
    if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
      endSnakeGame();
      return;
    }

    // Body collision
    for (let seg of snake) {
      if (seg.x === head.x && seg.y === head.y) {
        endSnakeGame();
        return;
      }
    }

    snake.unshift(head);

    // Food collision
    if (head.x === snakeFood.x && head.y === snakeFood.y) {
      snakeScore++;
      spawnFood();
      const scoreEl = document.getElementById("snake-score");
      if (scoreEl) scoreEl.textContent = snakeScore;

      if (snakeScore > snakeBest) {
        snakeBest = snakeScore;
        localStorage.setItem("game_snake_best", snakeBest);
        const bestEl = document.getElementById("snake-best");
        if (bestEl) bestEl.textContent = snakeBest;
      }

      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
      }
    } else {
      snake.pop();
    }

    drawSnakeCanvas();
  }

  function endSnakeGame() {
    snakeRunning = false;
    if (window._snakeInterval) clearInterval(window._snakeInterval);

    const overlay = document.getElementById("snake-overlay");
    if (overlay) {
      overlay.classList.remove("hidden");
      overlay.innerHTML = `
        <span class="text-3xl">💥</span>
        <p class="text-sm font-black text-rose-400">Игра окончена!</p>
        <p class="text-xs text-slate-300">Счёт: ${snakeScore}</p>
        <button onclick="window.GAMES.startSnakeGame()" class="mt-2 px-3 py-1.5 rounded-xl bg-emerald-600 text-white font-bold text-xs">Играть снова</button>
      `;
    }
  }

  function drawSnakeCanvas() {
    const canvas = document.getElementById("snake-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const cellPx = canvas.width / GRID_SIZE;

    // Clear background
    ctx.fillStyle = "#0f172a"; // dark slate
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw grid lines faintly
    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= GRID_SIZE; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cellPx, 0);
      ctx.lineTo(i * cellPx, canvas.height);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(0, i * cellPx);
      ctx.lineTo(canvas.width, i * cellPx);
      ctx.stroke();
    }

    // Draw Food (Apple)
    ctx.fillStyle = "#ef4444"; // red
    ctx.beginPath();
    ctx.arc((snakeFood.x + 0.5) * cellPx, (snakeFood.y + 0.5) * cellPx, cellPx * 0.4, 0, Math.PI * 2);
    ctx.fill();

    // Draw Snake
    snake.forEach((seg, i) => {
      ctx.fillStyle = i === 0 ? "#10b981" : "#34d399"; // emerald
      ctx.beginPath();
      ctx.roundRect(seg.x * cellPx + 1, seg.y * cellPx + 1, cellPx - 2, cellPx - 2, 4);
      ctx.fill();
    });
  }

  // ==============================================================================
  // GAME 4: CHESS (Шахматы - только онлайн дуэль на 2 игроков)
  // ==============================================================================
  let chessState = "lobby"; // 'lobby', 'loading', 'waiting', 'playing', 'finished', 'rejected'
  let chessRoomId = null;
  let chessRoomData = null;
  let chessOpponentName = "";
  let chessSelectedSquare = null; // e.g. "e2"
  let chessPendingPromotion = null; // { from: "e7", to: "e8" }
  let chessClassmatesList = [];
  let chessClassmatesFilter = "";
  let isChessLoadingClassmates = false;
  let chessPollTimer = null;
  let isChessPolling = false;
  let chessSelectedColor = "white"; // 'white' | 'black' | 'random'

  function setChessColor(color) {
    if (["white", "black", "random"].includes(color)) {
      chessSelectedColor = color;
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.selectionChanged();
      }
      renderGames();
    }
  }

  const CHESS_SYMBOLS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚"
  };

  const CHESS_FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];

  function initChess() {
    if (!chessRoomId) {
      chessState = "lobby";
      if (!isChessLoadingClassmates && chessClassmatesList.length === 0) {
        loadChessClassmates();
      }
    }
  }

  function parseFen(fen) {
    if (!fen) fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const parts = fen.split(" ");
    const rows = parts[0].split("/");
    const board = [];
    for (let r = 0; r < 8; r++) {
      const rowStr = rows[r] || "8";
      const row = [];
      for (let i = 0; i < rowStr.length; i++) {
        const ch = rowStr[i];
        if (ch >= "1" && ch <= "8") {
          const num = parseInt(ch, 10);
          for (let k = 0; k < num; k++) row.push("");
        } else {
          row.push(ch);
        }
      }
      board.push(row);
    }
    return board;
  }

  function rcToSquare(r, c) {
    return CHESS_FILES[c] + (8 - r);
  }

  function squareToRC(sq) {
    const file = sq.charAt(0);
    const rank = parseInt(sq.charAt(1), 10);
    const c = CHESS_FILES.indexOf(file);
    const r = 8 - rank;
    return { r, c };
  }

  function renderChessPiece(char) {
    if (!char) return "";
    const isWhite = char === char.toUpperCase();
    const glyph = CHESS_SYMBOLS[char] || char;
    return `
      <span class="select-none leading-none inline-block font-black text-2xl sm:text-3xl transition-transform transform group-active:scale-90 ${
        isWhite
          ? 'text-white drop-shadow-[0_2px_2px_rgba(0,0,0,0.95)]'
          : 'text-slate-900 drop-shadow-[0_1px_1px_rgba(255,255,255,0.7)]'
      }">
        ${glyph}
      </span>
    `;
  }

  function renderChessHTML() {
    return `
      <div class="theme-card rounded-3xl p-3 sm:p-4 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-sm space-y-3 max-w-sm mx-auto text-center">
        ${renderChessContentHTML()}
      </div>
    `;
  }

  function renderChessContentHTML() {
    if (chessState === "loading") {
      return `
        <div class="py-12 space-y-3">
          <div class="w-10 h-10 border-4 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p class="text-xs font-bold text-slate-500">Подключение к шахматной партии...</p>
        </div>
      `;
    }

    if (chessState === "waiting") {
      const oppName = chessOpponentName || (chessRoomData?.black?.name || chessRoomData?.white?.name) || "Одноклассник";
      const hostColor = chessRoomData?.host_color || (chessSelectedColor === "black" ? "black" : "white");
      const colorBadge = hostColor === "black"
        ? `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-800 text-white border border-slate-600 text-[10px] font-bold">⚫ Твой цвет: Черные</span>`
        : `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold">⚪ Твой цвет: Белые</span>`;

      return `
        <div class="py-8 space-y-4">
          <div class="w-16 h-16 rounded-3xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 flex items-center justify-center text-3xl mx-auto shadow-inner animate-pulse">
            ♟️
          </div>
          <div class="space-y-1.5">
            <h3 class="text-sm font-black text-slate-800 dark:text-white">Вызов отправлен: ${escapeHtml(oppName)}</h3>
            <div>${colorBadge}</div>
            <p class="text-[11px] text-slate-400 max-w-xs mx-auto pt-1">
              Бот отправил однокласснику приглашение с кнопкой входа. Ждем, пока он нажмет «Принять вызов»...
            </p>
          </div>
          <button
            onclick="window.GAMES.cancelChessGame()"
            class="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 font-bold text-xs transition-all active:scale-95">
            ❌ Отменить вызов
          </button>
        </div>
      `;
    }

    if (chessState === "rejected") {
      return `
        <div class="py-8 space-y-3">
          <div class="text-4xl">❌</div>
          <h3 class="text-sm font-black text-slate-800 dark:text-white">Вызов отклонен или отменен</h3>
          <p class="text-xs text-slate-400">Соперник не смог сыграть партию в этот раз.</p>
          <button
            onclick="window.GAMES.backToChessLobby()"
            class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition-all active:scale-95">
            🔙 Вернуться к списку
          </button>
        </div>
      `;
    }

    if (chessState === "playing" || chessState === "finished") {
      const yourRole = chessRoomData?.your_role; // 'white' | 'black' | null
      const isFlipped = yourRole === "black";
      const isYourTurn = chessRoomData?.is_your_turn;
      const isFinished = chessState === "finished";
      const board = parseFen(chessRoomData?.fen);

      const whiteName = chessRoomData?.white?.name || "Белые";
      const blackName = chessRoomData?.black?.name || "Черные";

      const oppName = isFlipped ? whiteName : blackName;
      const oppRole = isFlipped ? "white" : "black";
      const myName = isFlipped ? blackName : whiteName;

      const oppCaptured = (isFlipped ? chessRoomData?.captured_pieces?.by_white : chessRoomData?.captured_pieces?.by_black) || [];
      const myCaptured = (isFlipped ? chessRoomData?.captured_pieces?.by_black : chessRoomData?.captured_pieces?.by_white) || [];

      let statusHTML = "";
      if (isFinished) {
        const winner = chessRoomData?.winner;
        const reason = chessRoomData?.termination_reason;
        if (winner === "draw") {
          let reasonText = "Ничья";
          if (reason === "stalemate") reasonText = "Пат (Ничья)";
          else if (reason === "insufficient_material") reasonText = "Недостаточно фигур";
          else if (reason === "repetition") reasonText = "Троекратное повторение";
          else if (reason === "fifty_moves") reasonText = "Правило 50 ходов";
          statusHTML = `<div class="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-extrabold">🤝 ${reasonText}! Боевая ничья!</div>`;
        } else if (winner === yourRole) {
          const reasonText = reason === "resignation" ? "Соперник сдался" : "Мат сопернику";
          statusHTML = `<div class="p-2.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-extrabold animate-pulse">🏆 ПОБЕДА! ${reasonText}!</div>`;
        } else {
          const reasonText = reason === "resignation" ? "Вы сдались" : "Вам поставлен мат";
          statusHTML = `<div class="p-2.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-extrabold">😔 Поражение (${reasonText})</div>`;
        }
      } else {
        if (chessRoomData?.is_check) {
          if (isYourTurn) {
            statusHTML = `<div class="p-2 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-600 dark:text-rose-400 text-xs font-black animate-pulse">⚠️ ШАХ! Твой король атакован!</div>`;
          } else {
            statusHTML = `<div class="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-black">⚡ ШАХ сопернику!</div>`;
          }
        } else {
          if (isYourTurn) {
            statusHTML = `<div class="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-extrabold animate-pulse">🟢 Твой ход (${yourRole === 'white' ? 'Белые ♔' : 'Черные ♚'})</div>`;
          } else {
            statusHTML = `<div class="p-2 rounded-xl bg-slate-100 dark:bg-slate-700/60 text-slate-500 dark:text-slate-400 text-xs font-bold">⏳ Ход соперника (${oppName})...</div>`;
          }
        }
      }

      const legalMovesForSelected = chessSelectedSquare
        ? (chessRoomData?.legal_moves || []).filter(m => m.startsWith(chessSelectedSquare))
        : [];
      const legalTargetSquares = new Set(legalMovesForSelected.map(m => m.slice(2, 4)));

      const lastMove = chessRoomData?.last_move || "";
      const lastMoveFrom = lastMove.slice(0, 2);
      const lastMoveTo = lastMove.slice(2, 4);

      const rRange = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];
      const cRange = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];

      return `
        <!-- Top Player (Opponent) Bar -->
        <div class="flex items-center justify-between p-2 rounded-2xl bg-slate-100 dark:bg-slate-700/60 text-xs font-bold">
          <div class="flex items-center gap-1.5 min-w-0 pr-1">
            <span class="w-6 h-6 rounded-lg ${oppRole === 'white' ? 'bg-amber-100 text-amber-900 border border-amber-300' : 'bg-slate-800 text-white border border-slate-600'} flex items-center justify-center font-black text-xs shrink-0">
              ${oppRole === 'white' ? '♔' : '♚'}
            </span>
            <div class="text-left truncate">
              <div class="truncate text-slate-800 dark:text-white">${escapeHtml(oppName)}</div>
              <div class="text-[10px] text-slate-400 font-normal tracking-tight">
                ${oppCaptured.length > 0 ? oppCaptured.map(p => CHESS_SYMBOLS[p] || p).join(' ') : 'Без взятий'}
              </div>
            </div>
          </div>
          ${!isFinished && !isYourTurn ? '<span class="text-[10px] text-amber-500 font-black animate-pulse uppercase">Думает...</span>' : ''}
        </div>

        <!-- Status / Turn Banner -->
        ${statusHTML}

        <!-- 8x8 Chess Board -->
        <div class="w-full max-w-[320px] aspect-square mx-auto rounded-2xl overflow-hidden shadow-lg border-2 border-amber-950/40 select-none grid grid-cols-8 grid-rows-8 relative" style="touch-action: manipulation;">
          ${rRange.map(r => cRange.map(c => {
            const sq = rcToSquare(r, c);
            const piece = board[r][c];
            const isLight = (r + c) % 2 === 0;
            const isSelected = sq === chessSelectedSquare;
            const isLastMove = sq === lastMoveFrom || sq === lastMoveTo;
            const isLegalTarget = legalTargetSquares.has(sq);

            const isKingInCheck = chessRoomData?.is_check && (
              (chessRoomData.turn === "white" && piece === "K") ||
              (chessRoomData.turn === "black" && piece === "k")
            );

            let bgStyle = isLight ? "background-color: #f0d9b5;" : "background-color: #b58863;";
            if (isSelected) {
              bgStyle = "background-color: #cdd26a !important;";
            } else if (isKingInCheck) {
              bgStyle = "background: radial-gradient(circle, #ef4444 0%, #dc2626 70%, #991b1b 100%) !important;";
            } else if (isLastMove) {
              bgStyle = isLight ? "background-color: #d8ce66;" : "background-color: #aaa23a;";
            }

            return `
              <button
                id="chess-sq-${sq}"
                type="button"
                onclick="window.GAMES.chessSquareClick('${sq}')"
                style="${bgStyle}"
                class="w-full h-full p-0 m-0 relative flex items-center justify-center cursor-pointer transition-colors group">
                
                ${(c === (isFlipped ? 7 : 0)) ? `
                  <span class="absolute top-0.5 left-0.5 text-[8px] font-bold pointer-events-none opacity-60 ${isLight ? 'text-[#b58863]' : 'text-[#f0d9b5]'}">
                    ${8 - r}
                  </span>
                ` : ''}
                ${(r === (isFlipped ? 0 : 7)) ? `
                  <span class="absolute bottom-0 right-0.5 text-[8px] font-bold pointer-events-none opacity-60 ${isLight ? 'text-[#b58863]' : 'text-[#f0d9b5]'}">
                    ${CHESS_FILES[c]}
                  </span>
                ` : ''}

                ${renderChessPiece(piece)}

                ${isLegalTarget ? (
                  piece !== "" ? `
                    <div class="absolute inset-0.5 rounded-full border-2 border-rose-500/80 pointer-events-none animate-pulse"></div>
                  ` : `
                    <div class="w-3 h-3 rounded-full bg-emerald-600/60 pointer-events-none shadow-sm"></div>
                  `
                ) : ''}
              </button>
            `;
          }).join('')).join('')}
        </div>

        <!-- Pawn Promotion Picker Modal (if applicable) -->
        ${chessPendingPromotion ? `
          <div class="p-2.5 rounded-2xl bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 space-y-2">
            <div class="text-xs font-black text-amber-800 dark:text-amber-200">Превращение пешки в:</div>
            <div class="flex items-center justify-center gap-2">
              <button onclick="window.GAMES.choosePromotion('q')" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-700 shadow border text-2xl font-black active:scale-95">♕</button>
              <button onclick="window.GAMES.choosePromotion('r')" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-700 shadow border text-2xl font-black active:scale-95">♖</button>
              <button onclick="window.GAMES.choosePromotion('b')" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-700 shadow border text-2xl font-black active:scale-95">♗</button>
              <button onclick="window.GAMES.choosePromotion('n')" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-700 shadow border text-2xl font-black active:scale-95">♘</button>
            </div>
          </div>
        ` : ''}

        <!-- Bottom Player (You) Bar -->
        <div class="flex items-center justify-between p-2 rounded-2xl bg-slate-100 dark:bg-slate-700/60 text-xs font-bold">
          <div class="flex items-center gap-1.5 min-w-0 pr-1">
            <span class="w-6 h-6 rounded-lg ${yourRole === 'white' ? 'bg-amber-100 text-amber-900 border border-amber-300' : 'bg-slate-800 text-white border border-slate-600'} flex items-center justify-center font-black text-xs shrink-0">
              ${yourRole === 'white' ? '♔' : '♚'}
            </span>
            <div class="text-left truncate">
              <div class="truncate text-slate-800 dark:text-white">${escapeHtml(myName)} (Вы)</div>
              <div class="text-[10px] text-slate-400 font-normal tracking-tight">
                ${myCaptured.length > 0 ? myCaptured.map(p => CHESS_SYMBOLS[p] || p).join(' ') : 'Без взятий'}
              </div>
            </div>
          </div>
          ${!isFinished ? `
            <button
              onclick="window.GAMES.resignChessGame()"
              class="px-2.5 py-1 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-xs font-bold transition-all">
              🏳️ Сдаться
            </button>
          ` : ''}
        </div>

        <!-- Actions (Finished) -->
        ${isFinished ? `
          <div class="space-y-2 pt-1">
            ${chessRoomData?.rematch_requested_by ? `
              ${chessRoomData.rematch_requested_by === yourRole ? `
                <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-700 text-xs font-bold text-slate-500 flex items-center justify-center gap-1.5">
                  <span class="animate-spin">⏳</span> Ждем согласие соперника на реванш...
                </div>
              ` : `
                <button
                  onclick="window.GAMES.requestChessRematch()"
                  class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black text-xs shadow-md transition-all flex items-center justify-center gap-1.5">
                  <span>🔥</span> Соперник ждет реванш! Принять бой
                </button>
              `}
            ` : `
              <button
                onclick="window.GAMES.requestChessRematch()"
                class="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-black text-xs shadow-md transition-all flex items-center justify-center gap-1.5">
                <span>🔄</span> Предложить реванш (смена цвета)
              </button>
            `}
            <button
              onclick="window.GAMES.leaveChessGame()"
              class="w-full py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 text-slate-500 font-bold text-xs transition-all active:scale-95">
              🚪 Выйти в лобби
            </button>
          </div>
        ` : ''}
      `;
    }

    // Default: Lobby
    return `
      <div class="space-y-3">
        <div class="text-left px-1 space-y-0.5">
          <h3 class="text-xs font-black text-slate-800 dark:text-white flex items-center gap-1">
            <span>♟️</span> Шахматная онлайн-дуэль
          </h3>
          <p class="text-[11px] text-slate-400">
            Бот мгновенно пришлет однокласснику в Telegram кнопку входа в игру
          </p>
        </div>

        <!-- Color Selector: White / Random / Black -->
        <div class="p-2.5 rounded-2xl bg-slate-50 dark:bg-slate-700/40 border border-slate-200/80 dark:border-slate-700 space-y-1.5">
          <div class="text-left text-[11px] font-bold text-slate-600 dark:text-slate-300 flex items-center justify-between">
            <span>Выбор цвета:</span>
            <span class="text-[10px] font-medium text-amber-600 dark:text-amber-400">
              ${chessSelectedColor === 'white' ? 'Белые (ходишь первым)' : (chessSelectedColor === 'black' ? 'Черные (ходишь вторым)' : 'Случайный (50/50)')}
            </span>
          </div>
          <div class="grid grid-cols-3 gap-1.5">
            <button
              onclick="window.GAMES.setChessColor('white')"
              class="py-2 px-1 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1 active:scale-95 ${
                chessSelectedColor === 'white'
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-md border-2 border-amber-500 font-black'
                  : 'bg-white/60 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-600'
              }">
              <span class="text-base leading-none">⚪</span>
              <span>Белый</span>
            </button>
            <button
              onclick="window.GAMES.setChessColor('random')"
              class="py-2 px-1 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1 active:scale-95 ${
                chessSelectedColor === 'random'
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-md border-2 border-amber-500 font-black'
                  : 'bg-white/60 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-600'
              }">
              <span class="text-base leading-none">🎲</span>
              <span>Случайно</span>
            </button>
            <button
              onclick="window.GAMES.setChessColor('black')"
              class="py-2 px-1 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1 active:scale-95 ${
                chessSelectedColor === 'black'
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-md border-2 border-amber-500 font-black'
                  : 'bg-white/60 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-600'
              }">
              <span class="text-base leading-none">⚫</span>
              <span>Черный</span>
            </button>
          </div>
        </div>

        <!-- Search & Refresh -->
        <div class="flex items-center gap-1.5">
          <input
            type="text"
            id="chess-classmate-input"
            value="${escapeHtml(chessClassmatesFilter)}"
            oninput="window.GAMES.filterChessClassmates(this.value)"
            placeholder="🔍 Поиск одноклассника..."
            class="flex-1 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
          <button
            onclick="window.GAMES.refreshChessClassmates()"
            title="Обновить"
            class="p-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-500 hover:text-slate-800 dark:hover:text-white transition-all active:scale-95">
            🔄
          </button>
        </div>

        <!-- Classmates List Container -->
        <div id="chess-classmates-wrapper">
          ${isChessLoadingClassmates ? `
            <div class="py-8 text-center text-xs text-slate-400 space-y-2">
              <div class="w-6 h-6 border-2 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <span>Загрузка одноклассников...</span>
            </div>
          ` : renderChessClassmatesListHTML()}
        </div>
      </div>
    `;
  }

  function renderChessClassmatesListHTML() {
    const q = (chessClassmatesFilter || "").toLowerCase().trim();
    const filtered = chessClassmatesList.filter(c => {
      const name = (c.name || c.full_name || "").toLowerCase();
      return !q || name.includes(q);
    });

    if (filtered.length === 0) {
      return `
        <div class="py-8 text-center text-xs text-slate-400">
          ${q ? "Никого не найдено по запросу" : "Одноклассники не найдены"}
        </div>
      `;
    }

    return `
      <div id="chess-classmates-container" class="space-y-1.5 max-h-56 overflow-y-auto pr-1">
        ${filtered.map(c => {
          const name = c.name || c.full_name || "Одноклассник";
          const initial = name.charAt(0).toUpperCase();
          return `
            <div class="flex items-center justify-between p-2 rounded-2xl bg-slate-50 dark:bg-slate-700/50 border border-slate-200/60 dark:border-slate-700 hover:border-amber-400 dark:hover:border-amber-500/50 transition-all">
              <div class="flex items-center gap-2 min-w-0 pr-2">
                <div class="w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 font-black text-xs flex items-center justify-center shrink-0">
                  ${initial}
                </div>
                <div class="truncate text-left">
                  <div class="text-xs font-bold text-slate-800 dark:text-white truncate">${escapeHtml(name)}</div>
                  <div class="text-[10px] text-slate-400">11 «Б»</div>
                </div>
              </div>
              <button
                onclick="window.GAMES.inviteChessClassmate(${c.tg_id}, '${escapeHtml(name)}')"
                class="shrink-0 px-3 py-1.5 rounded-xl font-black text-xs bg-amber-600 hover:bg-amber-700 active:scale-95 text-white shadow-sm transition-all flex items-center gap-1">
                <span>♟️</span> Вызвать
              </button>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  async function loadChessClassmates() {
    if (isChessLoadingClassmates) return;
    isChessLoadingClassmates = true;

    const wrapper = document.getElementById("chess-classmates-wrapper");
    if (wrapper) {
      wrapper.innerHTML = `
        <div class="py-8 text-center text-xs text-slate-400 space-y-2">
          <div class="w-6 h-6 border-2 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <span>Загрузка одноклассников...</span>
        </div>
      `;
    }

    try {
      chessClassmatesList = await api.getClassmates();
    } catch (e) {
      console.warn("Could not load classmates for chess:", e);
      chessClassmatesList = [];
    } finally {
      isChessLoadingClassmates = false;
      const w = document.getElementById("chess-classmates-wrapper");
      if (w) {
        w.innerHTML = renderChessClassmatesListHTML();
      }
    }
  }

  function filterChessClassmates(val) {
    chessClassmatesFilter = val;
    const wrapper = document.getElementById("chess-classmates-wrapper");
    if (wrapper) {
      wrapper.innerHTML = renderChessClassmatesListHTML();
    }
  }

  async function inviteChessClassmate(tgId, oppName) {
    chessOpponentName = oppName;
    chessState = "waiting";
    renderGames();

    try {
      let myName = "Одноклассник";
      try {
        const me = await api.getMe();
        if (me && me.full_name) myName = me.full_name;
      } catch (e) {}

      const res = await api.inviteGame(tgId, myName, "chess", chessSelectedColor, oppName);
      chessRoomId = res.room_id;
      chessRoomData = res;
      startChessPolling();
    } catch (e) {
      alert("Не удалось отправить вызов в шахматы: " + (e.message || "Ошибка"));
      chessState = "lobby";
      renderGames();
    }
  }

  async function openChessOnlineRoom(roomId) {
    currentGame = "chess";
    chessRoomId = roomId;
    chessState = "loading";
    renderGames();

    try {
      let myName = "Игрок";
      try {
        const me = await api.getMe();
        if (me && me.full_name) myName = me.full_name;
      } catch (e) {}

      const room = await api.joinGameRoom(roomId, myName);
      chessRoomData = room;
      if (room.status === "finished") {
        chessState = "finished";
      } else if (room.status === "waiting") {
        chessState = "waiting";
      } else {
        chessState = "playing";
      }
      renderGames();
      startChessPolling();
    } catch (e) {
      console.error("Failed to join chess online room:", e);
      chessState = "rejected";
      renderGames();
    }
  }

  function chessSquareClick(sq) {
    if (!chessRoomData || chessRoomData.status !== "playing") return;
    if (!chessRoomData.is_your_turn) return;

    const board = parseFen(chessRoomData.fen);
    const { r, c } = squareToRC(sq);
    const piece = board[r][c];
    const yourRole = chessRoomData.your_role;
    const isMyPiece = piece && (
      (yourRole === "white" && piece === piece.toUpperCase()) ||
      (yourRole === "black" && piece === piece.toLowerCase())
    );

    if (chessSelectedSquare) {
      const legalMoves = (chessRoomData.legal_moves || []).filter(m => m.startsWith(chessSelectedSquare));
      const matchingMove = legalMoves.find(m => m.slice(2, 4) === sq);

      if (matchingMove) {
        const promoMoves = legalMoves.filter(m => m.slice(2, 4) === sq && m.length === 5);
        if (promoMoves.length > 0) {
          chessPendingPromotion = { from: chessSelectedSquare, to: sq };
          renderGames();
          return;
        }

        const uci = chessSelectedSquare + sq;
        chessSelectedSquare = null;
        sendChessMove(uci);
        return;
      }

      if (isMyPiece) {
        chessSelectedSquare = sq;
        if (window.Telegram?.WebApp?.HapticFeedback) {
          window.Telegram.WebApp.HapticFeedback.selectionChanged();
        }
        renderGames();
        return;
      }

      chessSelectedSquare = null;
      renderGames();
      return;
    }

    if (isMyPiece) {
      chessSelectedSquare = sq;
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.selectionChanged();
      }
      renderGames();
    }
  }

  function choosePromotion(pieceLetter) {
    if (!chessPendingPromotion) return;
    const uci = chessPendingPromotion.from + chessPendingPromotion.to + pieceLetter.toLowerCase();
    chessPendingPromotion = null;
    chessSelectedSquare = null;
    sendChessMove(uci);
  }

  async function sendChessMove(uci) {
    if (!chessRoomId) return;
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
    }

    try {
      const updated = await api.sendGameMove(chessRoomId, uci);
      handleChessRoomUpdate(updated);
    } catch (e) {
      console.warn("Chess move error:", e);
    }
  }

  async function resignChessGame() {
    if (!chessRoomId || chessRoomData?.status !== "playing") return;
    if (!confirm("Вы действительно хотите сдаться в этой партии?")) return;

    try {
      const updated = await api.resignGame(chessRoomId);
      handleChessRoomUpdate(updated);
    } catch (e) {
      alert("Ошибка при сдаче: " + (e.message || "Ошибка"));
    }
  }

  async function requestChessRematch() {
    if (!chessRoomId) return;
    try {
      const updated = await api.rematchGame(chessRoomId);
      handleChessRoomUpdate(updated);
      renderGames();
    } catch (e) {
      alert("Ошибка реванша: " + (e.message || "Ошибка"));
    }
  }

  async function cancelChessGame() {
    if (chessRoomId) {
      try {
        await api.cancelGame(chessRoomId);
      } catch (e) {}
    }
    stopChessPolling();
    chessRoomId = null;
    chessRoomData = null;
    chessState = "lobby";
    renderGames();
  }

  function leaveChessGame() {
    stopChessPolling();
    chessRoomId = null;
    chessRoomData = null;
    chessState = "lobby";
    renderGames();
  }

  function backToChessLobby() {
    stopChessPolling();
    chessRoomId = null;
    chessRoomData = null;
    chessState = "lobby";
    loadChessClassmates();
  }

  function startChessPolling() {
    stopChessPolling();
    isChessPolling = true;
    pollChessRoomState();
  }

  function stopChessPolling() {
    isChessPolling = false;
    if (chessPollTimer) {
      clearTimeout(chessPollTimer);
      chessPollTimer = null;
    }
  }

  async function pollChessRoomState() {
    if (!isChessPolling || !chessRoomId) return;

    try {
      const data = await api.getGameRoom(chessRoomId);
      handleChessRoomUpdate(data);
    } catch (e) {
      console.warn("Error polling chess room:", e);
    }

    if (isChessPolling && chessRoomId) {
      chessPollTimer = setTimeout(pollChessRoomState, 800);
    }
  }

  function handleChessRoomUpdate(data) {
    if (!data) return;
    const oldStatus = chessRoomData ? chessRoomData.status : null;
    const oldFen = chessRoomData ? chessRoomData.fen : null;
    const oldRematch = chessRoomData ? chessRoomData.rematch_requested_by : null;

    chessRoomData = data;

    if (data.status === "rejected" || data.status === "canceled") {
      stopChessPolling();
      chessState = "rejected";
      renderGames();
      return;
    }

    if (data.status === "waiting") {
      if (chessState !== "waiting") {
        chessState = "waiting";
        renderGames();
      }
      return;
    }

    if (data.status === "playing") {
      if (chessState !== "playing" || oldFen !== data.fen) {
        chessState = "playing";
        renderGames();
        if (window.Telegram?.WebApp?.HapticFeedback) {
          window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
        }
      }
      return;
    }

    if (data.status === "finished") {
      if (chessState !== "finished") {
        chessState = "finished";
        renderGames();
        if (window.Telegram?.WebApp?.HapticFeedback) {
          if (data.winner === data.your_role) {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
          } else if (data.winner === "draw") {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("warning");
          } else {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
          }
        }
      } else if (oldRematch !== data.rematch_requested_by) {
        renderGames();
      }
      return;
    }
  }

  window.GAMES = {
    init: initGames,
    switchGame: switchGame,
    cleanup: cleanupCurrentGame,
    // 2048
    reset2048: init2048,
    // Tic-Tac-Toe
    setTTTMode: setTTTMode,
    cellClickTTT: cellClickTTT,
    resetTTT: resetTTT,
    // Online Duel (Tic-Tac-Toe)
    openOnlineRoom: openOnlineRoom,
    inviteClassmate: inviteClassmate,
    makeOnlineMove: makeOnlineMove,
    requestRematch: requestRematch,
    cancelOnlineGame: cancelOnlineGame,
    leaveOnlineGame: leaveOnlineGame,
    backToLobby: backToLobby,
    filterClassmates: filterClassmates,
    refreshClassmates: loadClassmates,
    // Chess Online
    openChessOnlineRoom: openChessOnlineRoom,
    inviteChessClassmate: inviteChessClassmate,
    chessSquareClick: chessSquareClick,
    choosePromotion: choosePromotion,
    resignChessGame: resignChessGame,
    requestChessRematch: requestChessRematch,
    cancelChessGame: cancelChessGame,
    leaveChessGame: leaveChessGame,
    backToChessLobby: backToChessLobby,
    filterChessClassmates: filterChessClassmates,
    refreshChessClassmates: loadChessClassmates,
    setChessColor: setChessColor,
    // Snake
    startSnakeGame: startSnakeGame,
    setSnakeDir: setSnakeDir
  };
})();
