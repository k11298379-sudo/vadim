function renderTalentsTab() {
  const p = RPG_STATE.profile;
  if (!p) return `<div class="p-4 text-center text-white/50">Загрузка...</div>`;

  const talents = p.talents || {};
  const tPoints = p.talent_points || 0;
  const rebirths = p.rebirths || 0;

  // Definitions for talents
  const talentDefs = [
    { id: "lifesteal", name: "🩸 Вампиризм", desc: "Восстанавливает ХП от урона (+2% за лвл)", max: 5 },
    { id: "crit_mult", name: "💥 Крит. Урон", desc: "Увеличивает множитель крита (+25% за лвл)", max: 5 },
    { id: "cooldown", name: "⏳ Спешка", desc: "Снижает КД скиллов (на 6% за лвл)", max: 5 },
    { id: "dodge", name: "🍃 Уворот", desc: "Шанс увернуться от атаки босса (+4% за лвл)", max: 5 }
  ];

  let html = `
    <div class="p-3 bg-slate-900 min-h-screen text-slate-200">
      <div class="mb-4 bg-slate-800 p-4 rounded-xl border border-slate-700/50 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-r from-purple-900/40 to-blue-900/40 opacity-50"></div>
        <div class="relative z-10 flex justify-between items-center">
          <div>
            <h2 class="text-xl font-black text-white drop-shadow-md">Перерождение</h2>
            <div class="text-xs text-purple-300 mt-1">Текущий ранг: <span class="font-bold text-white">Перерождений: ${rebirths}</span></div>
            <div class="text-[10px] text-slate-400 mt-0.5">Каждое перерождение дает +10% ко всем характеристикам навсегда!</div>
          </div>
          <div>
            ${p.level >= 100 
              ? `<button onclick="doRebirthUI()" class="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg font-bold text-sm text-white shadow-lg shadow-purple-500/30 active:scale-95 transition-transform">СБРОС 100 ЛВЛ</button>`
              : `<button disabled class="px-4 py-2 bg-slate-700 rounded-lg font-bold text-sm text-slate-500 cursor-not-allowed">Нужен 100 ур.</button>`
            }
          </div>
        </div>
      </div>

      <div class="flex justify-between items-end mb-3 px-1">
        <h3 class="text-lg font-bold text-emerald-400">Дерево Талантов</h3>
        <div class="text-sm font-bold bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
          Очков: <span class="text-emerald-400">${tPoints}</span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3 pb-20">
  `;

  talentDefs.forEach(t => {
    const lvl = talents[t.id] || 0;
    const isMax = lvl >= t.max;
    const canUpgrade = tPoints > 0 && !isMax;

    html += `
        <div class="bg-slate-800 rounded-xl p-3 border border-slate-700 flex flex-col justify-between">
          <div>
            <div class="flex justify-between items-start mb-1">
              <div class="font-bold text-sm text-white leading-tight">${t.name}</div>
              <div class="text-xs font-bold ${isMax ? "text-amber-400" : "text-emerald-400"} bg-slate-900 px-1.5 py-0.5 rounded">
                ${lvl}/${t.max}
              </div>
            </div>
            <div class="text-[10px] text-slate-400 leading-snug mb-3">${t.desc}</div>
          </div>
          <button 
            onclick="upgradeTalentUI('${t.id}')"
            ${canUpgrade ? "" : "disabled"}
            class="w-full py-1.5 rounded-lg text-xs font-bold transition-all ${
              canUpgrade 
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 active:bg-emerald-500/40" 
                : "bg-slate-700/50 text-slate-500 border border-slate-700/50 cursor-not-allowed"
            }"
          >
            ${isMax ? "МАКСИМУМ" : "УЛУЧШИТЬ"}
          </button>
        </div>
    `;
  });

  html += `
      </div>

      <!-- PETS / FAMILIARS SECTION -->
      <div class="mb-3 px-1 flex justify-between items-end">
        <h3 class="text-lg font-bold text-amber-400">🐾 Боевые Питомцы</h3>
        <div class="text-[10px] text-slate-400">Летают с героем в 2D Арене</div>
      </div>

      <div class="space-y-2 pb-24">
        ${[
          { id: "dragon", icon: "🐉", name: "Дракончик Недр", bonus: "Огненный плевок", desc: "Каждые 2.5 сек выпускает самонаводящийся огненный шар в босса (250-400 урона)." },
          { id: "fairy", icon: "🧚", name: "Лесная Фея", bonus: "Аура Исцеления", desc: "Каждые 3 сек восстанавливает герою +45 HP и +15 MP в бою." },
          { id: "wolf", icon: "🐺", name: "Призрачный Волк", bonus: "Боевой вой", desc: "Пассивно дает герою +25% скорости атаки и +15% шанса критического удара." }
        ].map(pet => {
          const isSelected = (localStorage.getItem("rpg_active_pet") || "dragon") === pet.id;
          return `
            <div class="bg-slate-800/90 rounded-xl p-3 border ${isSelected ? 'border-amber-400/80 shadow-lg shadow-amber-500/10' : 'border-slate-700'} flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center text-2xl shadow-inner">
                  ${pet.icon}
                </div>
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="font-bold text-sm text-white">${pet.name}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-extrabold border border-amber-500/30">${pet.bonus}</span>
                  </div>
                  <div class="text-[10px] text-slate-400 mt-0.5 max-w-[210px] leading-tight">${pet.desc}</div>
                </div>
              </div>
              <button 
                onclick="selectPetUI('${pet.id}')"
                class="px-3 py-1.5 rounded-lg text-xs font-black transition-all ${
                  isSelected 
                    ? 'bg-amber-500 text-slate-950 shadow-md' 
                    : 'bg-slate-700/60 hover:bg-slate-700 text-slate-300 border border-slate-600'
                }"
              >
                ${isSelected ? 'В БОЮ' : 'ВЗЯТЬ'}
              </button>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;

  return html;
}

window.selectPetUI = function(petId) {
  localStorage.setItem("rpg_active_pet", petId);
  if (window.triggerHaptic) triggerHaptic("medium");
  if (typeof renderRoot === "function") renderRoot();
};

window.doRebirthUI = async function() {
  if (!confirm("Вы уверены? Ваш уровень сбросится до 1, но вы получите вечный бонус +10% ко всем статам!")) return;
  try {
    if (window.triggerHaptic) triggerHaptic("heavy");
    const res = await api.doRebirth();
    if (res.profile) {
      RPG_STATE.profile = res.profile;
      if (window.syncArenaPlayerStats) syncArenaPlayerStats();
      if (window.triggerHaptic) triggerHaptic("success");
      renderRoot();
    }
  } catch(e) {
    alert(e.message || "Ошибка перерождения");
  }
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
  } catch(e) {
    alert(e.message || "Ошибка улучшения таланта");
  }
};
