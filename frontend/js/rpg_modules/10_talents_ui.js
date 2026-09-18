// ============================================================
// 10_talents_ui.js — Новое Дерево Талантов Героев natarGRP
// 3 ветки (ATK / TANK / UTILITY) × 5 тиров = 15 узлов/герой
// ============================================================

const BRANCH_META = {
  atk:  { label: "🗡️ Атака",      color: "red",    bg: "from-red-950/80 to-red-900/40",    border: "border-red-500/50",   badge: "bg-red-600",  textColor: "text-red-300" },
  tank: { label: "🛡️ Выживание",  color: "blue",   bg: "from-blue-950/80 to-blue-900/40",  border: "border-blue-500/50",  badge: "bg-blue-600", textColor: "text-blue-300" },
  util: { label: "✨ Утилита",     color: "purple", bg: "from-purple-950/80 to-purple-900/40", border: "border-purple-500/50", badge: "bg-purple-600", textColor: "text-purple-300" },
};

const TIER_UNLOCK = { 1: 5, 2: 10, 3: 15, 4: 20, 5: 30 };

// Hero talent tree data (mirrored from backend talent_tree.py)
// Loaded dynamically from API or falls back to minimal local stub
let _cachedTalentTree = null;

function renderTalentsTab() {
  const p = RPG_STATE.profile;
  if (!p) return `<div class="p-4 text-center text-white/50">Загрузка...</div>`;

  const rebirths = (p.rebirth_info && p.rebirth_info.rank) || p.rebirths || 0;
  const rebirthMult = (p.rebirth_info && p.rebirth_info.multiplier) || 1.0;
  const essence = (p.rebirth_info && p.rebirth_info.essence) || p.rebirth_essence || 0;
  const charLvl = p.level || 1;
  const talentPts = p.talent_points || 0;

  let html = `<div class="p-3 bg-slate-900 min-h-screen text-slate-200 space-y-4">`;

  // === 1. REBIRTH BANNER ===
  html += `
    <div class="bg-gradient-to-r from-purple-950/80 via-slate-800 to-indigo-950/80 p-4 rounded-2xl border border-purple-500/40 shadow-lg relative overflow-hidden">
      <div class="relative z-10 flex justify-between items-center">
        <div>
          <div class="flex items-center gap-1.5">
            <h2 class="text-base font-black text-white drop-shadow-md">🌟 Алтарь Вознесения</h2>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/30 text-purple-300 font-extrabold border border-purple-400/30">Ранг ${rebirths}</span>
          </div>
          <div class="text-xs text-amber-300 mt-1 font-bold">Множитель статов: <span class="text-white">x${rebirthMult.toFixed(2)}</span> | ✨ Эссенция: <span class="text-white">${essence}</span></div>
          <div class="text-[10px] text-slate-400 mt-0.5">Доступно на 30, 40, 45 и 50 ур. Вещи и заточка сохраняются!</div>
        </div>
        <div>
          ${charLvl >= 30
            ? `<button onclick="doRebirthUI()" class="px-3 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl font-black text-xs text-white shadow-lg shadow-purple-500/30 active:scale-95">ВОЗНЕСЕНИЕ</button>`
            : `<button disabled class="px-3 py-1.5 bg-slate-800 rounded-xl font-bold text-[11px] text-slate-500 border border-slate-700 cursor-not-allowed">С 30 ур.</button>`
          }
        </div>
      </div>
    </div>`;

  // === 2. TALENT TREE HEADER ===
  html += `
    <div class="flex items-center justify-between px-1">
      <div>
        <h3 class="text-sm font-black text-amber-400 flex items-center gap-1.5">
          <span>⚔️</span> Дерево Талантов (${p.class_name || "Герой"})
        </h3>
        <p class="text-[10.5px] text-slate-400">Три ветки развития — выбирай свой путь!</p>
      </div>
      <div class="flex flex-col items-end gap-1">
        <span class="text-xs font-black px-2.5 py-1 rounded-xl bg-slate-800 border border-slate-700 text-amber-300">Ур. ${charLvl}</span>
        <span class="text-xs font-black px-2.5 py-1 rounded-xl ${talentPts > 0 ? 'bg-emerald-900/60 border-emerald-500/50 text-emerald-300 animate-pulse' : 'bg-slate-800 border-slate-700 text-slate-400'} border">⭐ ${talentPts} очк.</span>
      </div>
    </div>`;

  // === 3. TALENT TREE BRANCHES ===
  const treeData = _cachedTalentTree;
  if (!treeData) {
    html += `<div class="text-center text-slate-500 text-sm py-8">
      <div class="text-2xl mb-2">🌳</div>
      Загрузка дерева талантов...
      <br><button onclick="loadTalentTreeUI()" class="mt-3 px-4 py-2 bg-amber-600 rounded-xl text-white font-bold text-xs active:scale-95">Загрузить</button>
    </div>`;
  } else {
    const purchased = treeData.purchased || {};
    const branches = treeData.branches || {};

    html += `<div class="grid grid-cols-1 gap-3">`;
    for (const [branchKey, meta] of Object.entries(BRANCH_META)) {
      const nodes = (branches[branchKey] || []).slice().sort((a, b) => a.tier - b.tier);
      html += `
        <div class="bg-gradient-to-b ${meta.bg} rounded-2xl border ${meta.border} overflow-hidden shadow-lg">
          <div class="px-4 py-2.5 border-b ${meta.border} flex items-center justify-between">
            <h4 class="font-black text-sm ${meta.textColor}">${meta.label}</h4>
            <span class="text-[10px] text-slate-400">${nodes.filter(n => n.is_bought).length}/${nodes.length} куплено</span>
          </div>
          <div class="p-2 space-y-2">`;

      for (const node of nodes) {
        html += renderTalentNode(node, meta, charLvl, talentPts);
      }

      html += `</div></div>`;
    }
    html += `</div>`;
  }

  // === 4. PETS SECTION ===
  html += renderPetsSection(p);

  html += `</div>`;
  return html;
}

function renderTalentNode(node, meta, charLvl, talentPts) {
  const unlockLvl = TIER_UNLOCK[node.tier] || node.unlock_level || 5;
  const isLocked = charLvl < unlockLvl;
  const isReqMissing = !node.is_bought && !node.can_buy && node.req && !isLocked;

  let cardClass, badgeClass, btnHtml;
  if (node.is_bought) {
    cardClass = "bg-emerald-900/40 border-emerald-500/60";
    badgeClass = "bg-emerald-600 text-white";
    btnHtml = `<span class="text-[9px] font-black text-emerald-400">✓ КУПЛЕНО</span>`;
  } else if (isLocked) {
    cardClass = "bg-slate-900/30 border-slate-800/40 opacity-50";
    badgeClass = "bg-slate-700 text-slate-500";
    btnHtml = `<span class="text-[9px] text-slate-500">🔒 Нужен ${unlockLvl} ур.</span>`;
  } else if (isReqMissing) {
    cardClass = "bg-slate-900/40 border-slate-800/40 opacity-60";
    badgeClass = "bg-slate-700 text-slate-400";
    btnHtml = `<span class="text-[9px] text-slate-500">⛓ Нужен предыдущий талант</span>`;
  } else if (talentPts < (node.cost || 1)) {
    cardClass = "bg-slate-800/60 border-slate-700/60";
    badgeClass = `${meta.badge} opacity-60 text-white`;
    btnHtml = `<span class="text-[9px] text-amber-500/70">Нужно ${node.cost} очк.</span>`;
  } else {
    cardClass = "bg-slate-800/80 border-amber-500/40 shadow-amber-500/10 shadow-md";
    badgeClass = `${meta.badge} text-white animate-pulse`;
    btnHtml = `<button onclick="buyTalentNodeUI('${node.id}')" class="px-3 py-1 rounded-lg ${meta.badge} hover:brightness-110 active:scale-95 text-white font-black text-[10px] shadow-sm transition-all">КУПИТЬ (${node.cost}⭐)</button>`;
  }

  return `
    <div class="p-2.5 rounded-xl border transition-all ${cardClass}">
      <div class="flex items-start gap-2">
        <div class="w-9 h-9 rounded-xl ${node.is_bought ? 'bg-emerald-700/50' : 'bg-slate-900/60'} border border-slate-700 flex items-center justify-center text-xl shrink-0 shadow-inner">${node.icon}</div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5 mb-0.5">
            <span class="text-xs font-black text-white leading-tight">${node.name}</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded ${badgeClass} font-bold shrink-0">Т${node.tier}</span>
          </div>
          <div class="text-[10px] text-slate-400 leading-snug mb-1.5">${node.desc}</div>
          <div class="flex items-center justify-between">
            ${btnHtml}
          </div>
        </div>
      </div>
    </div>`;
}

function renderPetsSection(p) {
  const petDict = {
    "fairy":   { icon: "🧚", name: "Лесная Фея",          desc: "Снимает станы, +35% скорости бега" },
    "wolf":    { icon: "🐺", name: "Призрачный Волк",      desc: "Кровотечение 400 ед./сек" },
    "dragon":  { icon: "🐉", name: "Золотой Дракон",       desc: "Конус огня 1200 урона, +50% золота" },
    "phoenix": { icon: "🦅", name: "Пылающий Феникс",      desc: "Щит неуязвимости при смертельном ударе" },
    "slime":   { icon: "💧", name: "Капельный Слайм",      desc: "Лечит на 10% HP каждые 12с" },
    "donkey":  { icon: "🫏", name: "Ослик-Курьер Доты",    desc: "Носит рюкзак на 6 предметов, +40% к урону группы" },
  };

  let html = `
    <div class="space-y-2 pt-2 pb-20">
      <div class="flex items-center justify-between px-1">
        <div>
          <h3 class="text-sm font-black text-amber-400 flex items-center gap-1.5"><span>🐾</span> Боевые Питомцы</h3>
          <p class="text-[10px] text-slate-400">Летающий спутник атакует врагов и усиливает героя</p>
        </div>
        <button onclick="hatchPetUI()" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-400 active:scale-95 text-slate-950 font-black text-[11px] shadow-sm">🥚 ИНКУБАТОР (50 💎)</button>
      </div>
      <div class="space-y-1.5">`;

  const pets = p.pets || [];
  if (pets.length === 0) {
    html += `<div class="text-center text-slate-500 text-xs py-4 bg-slate-800/40 rounded-2xl border border-slate-800">У вас пока нет питомцев. Откройте яйцо в Инкубаторе!</div>`;
  }

  for (const pet of pets) {
    const pData = petDict[pet.type || pet.pet_id] || { icon: "🐾", name: pet.name || "Питомец", desc: "Боевой спутник" };
    const isSel = pet.is_equipped;
    html += `
      <div class="bg-slate-800/80 rounded-2xl p-3 border ${isSel ? 'border-amber-400 shadow-md shadow-amber-500/10' : 'border-slate-700/80'} flex items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center text-2xl shadow-inner relative">
            ${pData.icon}
            <div class="absolute -bottom-1 -right-1 bg-amber-500 text-slate-900 text-[9px] font-black px-1 rounded border border-amber-300">${pet.stars || 1}⭐</div>
          </div>
          <div>
            <div class="font-bold text-xs text-white">${pData.name}</div>
            <div class="text-[10px] text-slate-400 mt-0.5 leading-tight">${pData.desc}</div>
            <button onclick="upgradePetUI('${pet.uid}')" class="text-[10px] text-amber-400 underline mt-0.5 block font-semibold">Синтез 3-в-1 (нужно 3 шт, 10 💎)</button>
          </div>
        </div>
        <button onclick="equipPetUI('${pet.uid}')" class="px-3 py-1.5 rounded-xl text-xs font-black transition-all shrink-0 ${isSel ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-700 hover:bg-slate-600 text-slate-200'}">
          ${isSel ? 'НАДЕТ' : 'ВЗЯТЬ'}
        </button>
      </div>`;
  }

  html += `</div></div>`;
  return html;
}

// === EVENT HANDLERS ===

window.loadTalentTreeUI = async function() {
  try {
    const data = await api.getTalentTree();
    _cachedTalentTree = data;
    renderRoot();
  } catch (e) {
    alert("Ошибка загрузки дерева талантов: " + (e.message || e));
  }
};

window.buyTalentNodeUI = async function(nodeId) {
  try {
    if (window.triggerHaptic) triggerHaptic("medium");
    const res = await api.buyTalentNode(nodeId);
    if (res && res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      // Refresh tree cache
      _cachedTalentTree = await api.getTalentTree();
      if (window.triggerHaptic) triggerHaptic("success");
      renderRoot();
    }
  } catch (err) {
    if (window.triggerHaptic) triggerHaptic("error");
    alert(err.message || "Ошибка покупки таланта");
  }
};

window.chooseDotaTalentUI = async function(tier, choice) {
  try {
    if (window.triggerHaptic) triggerHaptic("medium");
    const res = await api.chooseDotaTalent(tier, choice);
    if (res && res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      if (window.triggerHaptic) triggerHaptic("success");
      renderRoot();
    }
  } catch (err) {
    if (window.triggerHaptic) triggerHaptic("error");
    alert(err.message || "Ошибка выбора таланта");
  }
};

window.hatchPetUI = async function() {
  try {
    if (window.triggerHaptic) triggerHaptic("medium");
    const res = await api.hatchPetCrate();
    if (res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.triggerHaptic) triggerHaptic("success");
      alert("Выпал питомец: " + (res.pet_cfg ? res.pet_cfg.name : "Новый питомец!"));
      renderRoot();
    }
  } catch(e) { alert(e.message || "Ошибка открытия яйца"); }
};

window.equipPetUI = async function(petUid) {
  try {
    if (window.triggerHaptic) triggerHaptic("light");
    const res = await api.equipPet(petUid);
    if (res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      const eqPet = (res.profile.pets || []).find(p => p.is_equipped);
      if (eqPet) localStorage.setItem("rpg_active_pet", eqPet.type || eqPet.pet_id);
      else localStorage.removeItem("rpg_active_pet");
      renderRoot();
    }
  } catch(e) { alert(e.message || "Ошибка экипировки"); }
};

window.selectPetUI = window.equipPetUI;

window.upgradePetUI = async function(petUid) {
  try {
    if (window.triggerHaptic) triggerHaptic("medium");
    const res = await api.upgradePet(petUid);
    if (res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      if (window.triggerHaptic) triggerHaptic("success");
      alert("Питомец успешно улучшен!");
      renderRoot();
    }
  } catch(e) { alert(e.message || "Ошибка улучшения питомца"); }
};

window.doRebirthUI = async function() {
  if (!confirm("Совершить Вознесение? Уровень сбросится до 1, но вы сохраните все предметы, заточку, питомцев и получите постоянный множитель статов!")) return;
  try {
    if (window.triggerHaptic) triggerHaptic("heavy");
    const res = await api.doRebirth();
    if (res.profile) {
      RPG_STATE.profile = res.profile;
      if (typeof ARENA !== "undefined") {
        ARENA.waveNumber = 1;
        ARENA.totalCreepsSpawned = 0;
        ARENA.creepsKilledInWave = 0;
        ARENA.creeps = [];
      }
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      if (window.triggerHaptic) triggerHaptic("success");
      _cachedTalentTree = null; // reset cache on rebirth
      renderRoot();
    }
  } catch(e) { alert(e.message || "Ошибка перерождения"); }
};

window.upgradeTalentUI = async function(talentId) {
  try {
    if (window.triggerHaptic) triggerHaptic("light");
    const res = await api.upgradeTalent(talentId);
    if (res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      renderRoot();
    }
  } catch(e) { alert(e.message || "Ошибка улучшения таланта"); }
};

// Auto-load talent tree data when tab opens
window._talentsTabAutoLoad = function() {
  if (!_cachedTalentTree && RPG_STATE.profile) {
    api.getTalentTree().then(data => {
      _cachedTalentTree = data;
      renderRoot();
    }).catch(() => {});
  }
};
