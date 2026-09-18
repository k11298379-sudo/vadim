const DOTA_HERO_TALENTS_FALLBACK = {
  pudge: {
    10: { left: "+25 к скорости бега", right: "+4 к броне" },
    15: { left: "+12% к замедлению от Rot", right: "+2.0x урона к Meat Hook" },
    20: { left: "+0.8 STR за заряд Flesh Heap", right: "-4с кулдауна Meat Hook" },
    25: { left: "Rot лечит Паджа вместо урона", right: "1.8x длительность и вампиризм Dismember" }
  },
  juggernaut: {
    10: { left: "+5 к броне", right: "+20 к скорости бега" },
    15: { left: "+25 к скорости атаки", right: "+1.2% к лечению Healing Ward" },
    20: { left: "+160 урона к Blade Fury", right: "+8% к шансу Blade Dance" },
    25: { left: "+1.0с длительности Omnislash", right: "+450 к здоровью" }
  },
  phantom_assassin: {
    10: { left: "+150 к дальности каста", right: "+15 к урону" },
    15: { left: "+25% к вампиризму", right: "+250 к здоровью" },
    20: { left: "-1.5с КД Stifling Dagger", right: "+25% к уклонению Blur" },
    25: { left: "+7% к шансу Coup de Grace", right: "Двойной Stifling Dagger" }
  },
  shadow_fiend: {
    10: { left: "+20 к скорости атаки", right: "+8% к силе заклинаний" },
    15: { left: "+80 к урону Shadowraze", right: "+3 к душам за убийство" },
    20: { left: "+2 души к макс. запасу", right: "-3с кулдауна Shadowraze" },
    25: { left: "Shadowraze накладывает страх", right: "+30% к урону от Requiem" }
  },
  invoker: {
    10: { left: "+40 к урону Chaos Meteor", right: "+2 к макс. духам Forge" },
    15: { left: "-8с КД Cold Snap", right: "+1 к силе всех сфер" },
    20: { left: "+35 к урону Alacrity", right: "-10с КД Tornado" },
    25: { left: "Катаклизм (Sun Strike по всем)", right: "Радиальный Deafening Blast" }
  },
  wraith_king: {
    10: { left: "+20 к скорости атаки", right: "+1.5с стана Wraithfire" },
    15: { left: "+6 к призыву скелетов", right: "+15 к силе" },
    20: { left: "Реинкарнация без расхода маны", right: "+25% к вампиризму" },
    25: { left: "+25% к шансу крита", right: "Двойной урон скелетов" }
  },
  anti_mage: {
    10: { left: "+9 к силе", right: "+15 к скорости атаки" },
    15: { left: "-1с КД Blink", right: "+300 к дальности Blink" },
    20: { left: "+15% к защите от магии", right: "+200 к урону Mana Void" },
    25: { left: "+20% к сжиганию маны", right: "Щит Counterspell союзникам" }
  },
  leshrac: {
    10: { left: "+4 к броне", right: "+40 к урону Pulse Nova" },
    15: { left: "+80 к радиусу Split Earth", right: "+15% к вампиризму заклинаний" },
    20: { left: "+25% к урону Lightning Storm", right: "+400 к мане" },
    25: { left: "+30 взрывов Diabolic Edict", right: "Pulse Nova замедляет на 25%" }
  }
};

function renderTalentsTab() {
  const p = RPG_STATE.profile;
  if (!p) return `<div class="p-4 text-center text-white/50">Загрузка...</div>`;

  const heroKey = (p.hero_class || "pudge").toLowerCase();
  const heroTalents = p.hero_talents || DOTA_HERO_TALENTS_FALLBACK[heroKey] || DOTA_HERO_TALENTS_FALLBACK["pudge"];
  const dotaTalents = (p.talents && p.talents.dota_talents) ? p.talents.dota_talents : {};
  const charLvl = p.level || 1;
  const rebirths = p.rebirths || (p.rebirth_info && p.rebirth_info.rank) || 0;
  const rebirthMult = (p.rebirth_info && p.rebirth_info.multiplier) || 1.0;
  const essence = (p.rebirth_info && p.rebirth_info.essence) || p.rebirth_essence || 0;
  const tiers = [25, 20, 15, 10];

  let html = `
    <div class="p-3 bg-slate-900 min-h-screen text-slate-200 space-y-4">
      <!-- 1. REBIRTH & ASCENSION BANNER -->
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
      </div>

      <!-- 2. DOTA 2 VERTICAL TALENT TREE -->
      <div class="space-y-2">
        <div class="flex items-center justify-between px-1">
          <div>
            <h3 class="text-sm font-black text-amber-400 flex items-center gap-1.5">
              <span>🧬</span> Древо Талантов Dota 2 (${p.class_name || "Герой"})
            </h3>
            <p class="text-[10.5px] text-slate-400">Выберите 1 из 2 способностей на каждом рубеже</p>
          </div>
          <span class="text-xs font-black px-2.5 py-1 rounded-xl bg-slate-800 border border-slate-700 text-amber-300">
            Ур. ${charLvl}
          </span>
        </div>

        <!-- Vertical Tree Container -->
        <div class="relative py-2 space-y-3 bg-slate-950/60 p-3 rounded-2xl border border-slate-800 shadow-inner">
          <!-- Central Connecting Line -->
          <div class="absolute left-1/2 top-5 bottom-5 w-0.5 -translate-x-1/2 bg-gradient-to-b from-amber-500/50 via-amber-600/30 to-slate-700/30 pointer-events-none"></div>

          ${tiers.map(tier => {
            const tData = heroTalents[tier] || { left: `Талант A (+${tier})`, right: `Талант B (+${tier})` };
            const isUnlocked = charLvl >= tier;
            const chosen = dotaTalents[tier] || dotaTalents[String(tier)] || null;

            const isLeftChosen = chosen === "left";
            const isRightChosen = chosen === "right";

            let centerBadgeClass = "bg-slate-800 text-slate-500 border-slate-700";
            if (chosen) {
              centerBadgeClass = "bg-amber-500 text-slate-950 font-black border-amber-300 ring-2 ring-amber-500/40 shadow-lg shadow-amber-500/30";
            } else if (isUnlocked) {
              centerBadgeClass = "bg-emerald-500 text-slate-950 font-black border-emerald-300 animate-pulse";
            }

            return `
              <div class="relative z-10 flex items-center gap-2">
                <!-- Left Talent Option -->
                <div class="flex-1">
                  <div class="p-2.5 rounded-xl border transition-all ${
                    isLeftChosen
                      ? "bg-amber-500/20 border-amber-400 text-amber-200 shadow-md shadow-amber-500/10"
                      : (isRightChosen
                          ? "bg-slate-900/40 border-slate-800 text-slate-600 opacity-40"
                          : (isUnlocked
                              ? "bg-slate-800/90 border-emerald-500/60 text-white hover:border-emerald-400"
                              : "bg-slate-900/30 border-slate-800/40 text-slate-600 opacity-50"))
                  }">
                    <div class="text-[11px] font-bold leading-snug">${tData.left}</div>
                    ${!chosen && isUnlocked
                      ? `<button onclick="chooseDotaTalentUI(${tier}, 'left')" class="mt-1.5 w-full py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-black text-[10px] shadow-sm">
                          ВЫБРАТЬ 👈
                        </button>`
                      : (isLeftChosen ? `<span class="mt-1 inline-block text-[9px] font-black text-amber-400">✓ ВЫБРАНО</span>` : "")
                    }
                  </div>
                </div>

                <!-- Central Level Circle -->
                <div class="w-9 h-9 rounded-full shrink-0 border-2 flex items-center justify-center text-xs font-black shadow-md ${centerBadgeClass}">
                  ${tier}
                </div>

                <!-- Right Talent Option -->
                <div class="flex-1">
                  <div class="p-2.5 rounded-xl border transition-all text-right ${
                    isRightChosen
                      ? "bg-amber-500/20 border-amber-400 text-amber-200 shadow-md shadow-amber-500/10"
                      : (isLeftChosen
                          ? "bg-slate-900/40 border-slate-800 text-slate-600 opacity-40"
                          : (isUnlocked
                              ? "bg-slate-800/90 border-emerald-500/60 text-white hover:border-emerald-400"
                              : "bg-slate-900/30 border-slate-800/40 text-slate-600 opacity-50"))
                  }">
                    <div class="text-[11px] font-bold leading-snug">${tData.right}</div>
                    ${!chosen && isUnlocked
                      ? `<button onclick="chooseDotaTalentUI(${tier}, 'right')" class="mt-1.5 w-full py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-black text-[10px] shadow-sm">
                          👉 ВЫБРАТЬ
                        </button>`
                      : (isRightChosen ? `<span class="mt-1 inline-block text-[9px] font-black text-amber-400">✓ ВЫБРАНО</span>` : "")
                    }
                  </div>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </div>

      <!-- 3. PETS / FAMILIARS SECTION -->
      <div class="space-y-2 pt-2 pb-20">
        <div class="flex items-center justify-between px-1">
          <div>
            <h3 class="text-sm font-black text-amber-400 flex items-center gap-1.5">
              <span>🐾</span> Боевые Питомцы Доты
            </h3>
            <p class="text-[10px] text-slate-400">Летающий спутник атакует врагов и усиливает героя</p>
          </div>
          <button onclick="hatchPetUI()" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-400 active:scale-95 text-slate-950 font-black text-[11px] shadow-sm">
            🥚 ИНКУБАТОР (50 💎)
          </button>
        </div>

        <div class="space-y-1.5">
          ${(p.pets || []).length === 0 ? `<div class="text-center text-slate-500 text-xs py-4 bg-slate-800/40 rounded-2xl border border-slate-800">У вас пока нет питомцев. Откройте яйцо в Инкубаторе!</div>` : ""}
          ${(p.pets || []).map(pet => {
            const petDict = {
              "fairy": { icon: "🧚", name: "Лесная Фея", desc: "Снимает станы, +35% скорости бега" },
              "wolf": { icon: "🐺", name: "Призрачный Волк", desc: "Кровотечение 400 ед./сек" },
              "dragon": { icon: "🐉", name: "Золотой Дракон", desc: "Конус огня 1200 урона, +50% золота" },
              "phoenix": { icon: "🦅", name: "Пылающий Феникс", desc: "Щит неуязвимости при смертельном ударе" },
              "slime": { icon: "💧", name: "Капельный Слайм", desc: "Лечит на 10% HP каждые 12с" },
              "donkey": { icon: "🫏", name: "Ослик-Курьер Доты", desc: "Носит рюкзак на 6 предметов, +40% к урону группы" }
            };
            const pData = petDict[pet.type || pet.pet_id] || { icon: "🐾", name: pet.name || "Питомец", desc: "Боевой спутник" };
            const isSelected = pet.is_equipped;
            return `
              <div class="bg-slate-800/80 rounded-2xl p-3 border ${isSelected ? 'border-amber-400 shadow-md shadow-amber-500/10' : 'border-slate-700/80'} flex items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                  <div class="w-11 h-11 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center text-2xl shadow-inner relative">
                    ${pData.icon}
                    <div class="absolute -bottom-1 -right-1 bg-amber-500 text-slate-900 text-[9px] font-black px-1 rounded border border-amber-300">
                      ${pet.stars || 1}⭐
                    </div>
                  </div>
                  <div>
                    <div class="font-bold text-xs text-white">${pData.name}</div>
                    <div class="text-[10px] text-slate-400 mt-0.5 leading-tight">${pData.desc}</div>
                    <button onclick="upgradePetUI('${pet.uid}')" class="text-[10px] text-amber-400 underline mt-0.5 block font-semibold">
                      Синтез 3-в-1 (нужно 3 шт, 10 💎)
                    </button>
                  </div>
                </div>
                <button onclick="equipPetUI('${pet.uid}')" class="px-3 py-1.5 rounded-xl text-xs font-black transition-all shrink-0 ${
                  isSelected ? 'bg-amber-500 text-slate-950 shadow-md' : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                }">
                  ${isSelected ? 'НАДЕТ' : 'ВЗЯТЬ'}
                </button>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    </div>
  `;

  return html;
}

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
  } catch(e) {
    alert(e.message || "Ошибка открытия яйца");
  }
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
  } catch(e) {
    alert(e.message || "Ошибка экипировки");
  }
};

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
  } catch(e) {
    alert(e.message || "Ошибка улучшения питомца");
  }
};

window.selectPetUI = window.equipPetUI;

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
