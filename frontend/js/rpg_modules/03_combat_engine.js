  function applyDamageToBoss(boss, rawDmg, isCrit) {
    if (!boss || boss.hp <= 0) return 0;

    const p = ARENA.player;
    const stats = RPG_STATE.profile?.stats || {};
    const eq = RPG_STATE.profile?.equipment || {};

      // Boss defense: stored on entity, or fallback by tier
    const BOSS_DEF_BY_TIER = {
      golem: 35, lich: 50, tormentor: 75, dragon: 105, pudge_boss: 140,
      faceless_void: 180, roshan: 230, tidehunter: 290, sf_boss: 370,
      necrophos: 460, terrorblade: 570, invoker_boss: 700, chaos_knight: 860,
      dark_tormentor: 1050, storm_spirit: 1300, doom: 1600, primal_beast: 1950,
      phantom_roshan: 2400, tinker_boss: 3000, enigma: 3800
    };
    let bossDefense = boss.defense !== undefined ? boss.defense : 35;
    if (!boss.defense) {
      const bId = ((boss.bossType || boss.id || boss.name) || "golem").toLowerCase();
      for (const [k, v] of Object.entries(BOSS_DEF_BY_TIER)) {
        if (bId.includes(k)) { bossDefense = v; break; }
      }
    }

    // Passive Items on Boss: Desolator & Assault Cuirass Minus Armor
    const hasDeso = Object.values(eq).some(it => it && (it.name?.includes("Desolator") || it.name?.includes("Опустошитель") || it.bonus?.minus_armor));
    const hasAC = Object.values(eq).some(it => it && (it.name?.includes("Assault") || it.name?.includes("Штурма") || it.bonus?.minus_armor_aura));
    if (hasDeso) {
      if (!boss.desoDebuff) {
        spawnFloatingText(boss.x, boss.y - 30, "🩸 -10 БРОНИ (DESOLATOR)", "#dc2626");
      }
      boss.desoDebuff = 300; // 5 seconds debuff
    }
    const totalArmorShred = (boss.desoDebuff > 0 ? 10 : 0) + (hasAC ? 10 : 0);
    const effectiveArmor = Math.max(0, bossDefense - totalArmorShred);

    // Hyperbolic armor reduction: DR = armor / (armor + 100)
    const armorDR = effectiveArmor / (effectiveArmor + 100);

    // Apply defense reduction to raw damage
    let afterArmor = Math.max(1, Math.floor(rawDmg * (1.0 - armorDR)));

    // Passive Item: MKB True Strike & Pure Bonus (+120 pure damage that ignores armor)
    const hasMkb = Object.values(eq).some(it => it && (it.name?.includes("Monkey") || it.name?.includes("Обезьян") || it.bonus?.pure_proc));
    if (hasMkb && Math.random() < 0.75) {
      afterArmor += 120;
      spawnFloatingText(boss.x, boss.y - 40, "🎯 MKB +120 ПИРС!", "#38bdf8");
    }

    // Passive Item: Mjollnir Chain Lightning (25% chance for 220 electric burst)
    const hasMjollnir = Object.values(eq).some(it => it && (it.name?.includes("Mjollnir") || it.name?.includes("Мьёльнир") || it.bonus?.lightning_proc));
    if (hasMjollnir && Math.random() < 0.25) {
      afterArmor += 220;
      spawnFloatingText(boss.x, boss.y - 35, "⚡ МЬЁЛЬНИР -220!", "#38bdf8");
      if (!ARENA.shockwaves) ARENA.shockwaves = [];
      ARENA.shockwaves.push({ x: boss.x, y: boss.y, radius: 15, maxRadius: 55, alpha: 0.9, color: "#38bdf8" });
    }

    // Passive Item: Eye of Skadi (Slows boss movement and attacks by 40%)
    const hasSkadi = Object.values(eq).some(it => it && (it.name?.includes("Skadi") || it.name?.includes("Скади") || it.bonus?.frost_slow));
    if (hasSkadi) {
      if (!boss.skadiSlow) {
        spawnFloatingText(boss.x, boss.y - 25, "❄️ СКАДИ -40% СКОРОСТЬ", "#38bdf8");
      }
      boss.skadiSlow = 240;
      boss.speed = Math.max(0.70, (boss.baseSpeed || 1.45) * 0.60);
    }

    // Stagger bonus (+50% damage when boss is staggered / poise broken)
    const staggerMult = boss.isStaggered ? 1.5 : 1.0;

    // Passive Item: Daedalus Crit Multiplier
    const hasDaedalus = Object.values(eq).some(it => it && (it.name?.includes("Daedalus") || it.name?.includes("Даэдалус") || it.bonus?.crit_mult));
    let critMult = isCrit ? (hasDaedalus ? 2.5 : 1.5) : 1.0;

    let finalDmg = Math.max(1, Math.floor(afterArmor * staggerMult * critMult));

    // DPS THROTTLE (anti-cheat ceiling per second):
    // Scales dynamically: max 2.5% HP/sec (normal) or 5.0% HP/sec (staggered)
    const curSec = Math.floor((ARENA.frameCount || 0) / 60);
    if (boss._dmgWindowSec !== curSec) {
      boss._dmgWindowSec = curSec;
      boss._dmgTakenThisSec = 0;
    }

    const secCapPct = boss.isStaggered ? 0.050 : 0.025;
    const maxSecDmg = Math.max(5000, Math.floor(boss.maxHp * secCapPct));
    const roomLeft = Math.max(0, maxSecDmg - (boss._dmgTakenThisSec || 0));

    if (roomLeft <= 0) {
      finalDmg = Math.max(1, Math.floor(finalDmg * 0.08));
    } else if (finalDmg > roomLeft) {
      const excess = finalDmg - roomLeft;
      finalDmg = roomLeft + Math.floor(excess * 0.12);
    }

    boss._dmgTakenThisSec = (boss._dmgTakenThisSec || 0) + finalDmg;
    boss.hp = Math.max(0, boss.hp - finalDmg);

    // Passive Item: Satanic & General Lifesteal (capped per hit to prevent infinite invulnerability)
    const lifestealPct = stats.lifesteal || 0;
    if (p && lifestealPct > 0) {
      const pMax = p.maxHp || 500;
      const rawHeal = Math.floor(finalDmg * (lifestealPct / 100));
      const heal = Math.max(1, Math.min(Math.floor(pMax * 0.08), rawHeal));
      p.currentHp = Math.min(pMax, p.currentHp + heal);
      if (ARENA.frameCount % 10 === 0) {
        spawnFloatingText(p.x, p.y - 25, `+${heal} HP 🩸`, "#22c55e");
      }
    }

    // BOSS PHASES (Epic Boss Phase Transitions):
    // Phase 2 at 66% HP: Boss Enrages, gains speed and a radial shockwave!
    const hpRatio = boss.hp / boss.maxHp;
    if (hpRatio <= 0.66 && !boss._phase2Triggered) {
      boss._phase2Triggered = true;
      boss.enrageStage = "angry";
      boss.speed = (boss.speed || 1.4) * 1.15;
      spawnFloatingText(boss.x, boss.y - 45, "🔥 БОСС ВПАДАЕТ В ЯРОСТЬ! ФАЗА 2!", "#ea580c");
      triggerHaptic("heavy");
      if (ARENA.cameraTrauma !== undefined) ARENA.cameraTrauma = 0.65;
      if (!ARENA.shockwaves) ARENA.shockwaves = [];
      ARENA.shockwaves.push({ x: boss.x, y: boss.y, radius: 10, maxRadius: 90, alpha: 1.0, color: "#ea580c" });
    }
    // Phase 3 at 33% HP: Desperation Frenzy!
    if (hpRatio <= 0.33 && !boss._phase3Triggered) {
      boss._phase3Triggered = true;
      boss.enrageStage = "enraged";
      boss.speed = (boss.speed || 1.4) * 1.20;
      spawnFloatingText(boss.x, boss.y - 45, "⚡ СМЕРТЕЛЬНАЯ ФАЗА! БОСС БЕЗУМЕН!", "#ef4444");
      triggerHaptic("heavy");
      if (ARENA.cameraTrauma !== undefined) ARENA.cameraTrauma = 0.85;
      if (!ARENA.shockwaves) ARENA.shockwaves = [];
      ARENA.shockwaves.push({ x: boss.x, y: boss.y, radius: 10, maxRadius: 120, alpha: 1.0, color: "#ef4444" });
    }

    if (boss.hp <= 0 && ARENA.isRaidBossBattle && ARENA.waveState !== "boss_victory") {
      handleRaidBossDefeat();
    }

    return finalDmg;
  }

  // UNIVERSAL SAFE DAMAGE: Routes all damage through applyDamageToBoss if target is a boss!
  function safeDamageCreep(c, rawDmg, isCrit) {
    if (!c || c.hp <= 0) return 0;
    if (c.isBoss) {
      return applyDamageToBoss(c, rawDmg, isCrit);
    }
    const dmg = Math.max(1, rawDmg);
    c.hp -= dmg;
    return dmg;
  }

  function calculateBossAttackDamage(boss, baseMult = 1.0) {
    if (!boss) return 50;
    const p = ARENA.player;
    const stats = RPG_STATE.profile?.stats || {};
    const def = Math.max(0, stats.defense || 5);

    // Real boss attack: from entity, template, or tier scaling fallback
    const BOSS_TIER_ATK = {
      golem: 140, lich: 210, tormentor: 320, dragon: 500, pudge_boss: 800,
      faceless_void: 1250, roshan: 1950, tidehunter: 3000, sf_boss: 4600,
      necrophos: 7000, terrorblade: 11000, invoker_boss: 17500, chaos_knight: 26500,
      dark_tormentor: 42000, storm_spirit: 64000, doom: 98000, primal_beast: 150000,
      phantom_roshan: 230000, tinker_boss: 350000, enigma: 500000
    };
    let bossAtk = boss.atk || boss.baseAtk;
    if (!bossAtk) {
      const bId = ((boss && (boss.id || boss.bossType || boss.name)) || "golem").toLowerCase();
      for (const [k, v] of Object.entries(BOSS_TIER_ATK)) {
        if (bId.includes(k)) { bossAtk = v; break; }
      }
      bossAtk = bossAtk || 140;
    }

    // Phase Enrage multiplier (when boss is enraged/furious/angry)
    let enrageMult = 1.0;
    if (boss.enrageStage === "enraged") enrageMult = 1.40;
    else if (boss.enrageStage === "furious") enrageMult = 1.25;
    else if (boss.enrageStage === "angry") enrageMult = 1.15;

    let rawDmg = Math.floor(bossAtk * baseMult * enrageMult);

    // Hyperbolic player defense reduction: DR = def / (def + 80), max 80%
    const dr = Math.min(0.80, (def * 1.0) / (def + 80));
    let finalDmg = Math.max(10, Math.floor(rawDmg * (1.0 - dr)));

    if (p && p.isBlocking) {
      finalDmg = Math.floor(finalDmg * 0.40);
    }

    return finalDmg;
  }

  function applyDamageToPlayer(rawDmg, attackType = "normal") {
    const p = ARENA.player;
    if (!p || (p.isInvulnerable && p.isInvulnerable > 0)) return 0;

    const stats = RPG_STATE.profile?.stats || {};
    const eq = RPG_STATE.profile?.equipment || {};

    // 1. Passive Item: Butterfly / Agility Evasion (dodge chance)
    const dodgeChance = Math.min(70, stats.dodge_chance || 0);
    if (dodgeChance > 0 && Math.random() * 100 < dodgeChance) {
      spawnFloatingText(p.x, p.y - 25, "💨 УВОРОТ! (БАБОЧКА)", "#38bdf8");
      triggerHaptic("light");
      return 0; // Completely dodge incoming attack!
    }

    // 2. Passive Item: Radiance Blind (17% chance boss misses attack)
    const hasRadiance = Object.values(eq).some(it => it && (it.name?.includes("Radiance") || it.name?.includes("Сияние") || it.bonus?.miss_aura));
    if (hasRadiance && Math.random() < 0.17) {
      spawnFloatingText(p.x, p.y - 25, "💨 ПРОМАХ БОССА! (РАДИАНС)", "#f59e0b");
      triggerHaptic("light");
      return 0; // Boss blinded!
    }

    let finalDmg = Math.max(1, rawDmg);

    // 3. Passive Item: Vanguard / Crimson Guard Damage Block (70% chance to block 80 dmg)
    const damageBlock = stats.damage_block || 0;
    if (damageBlock > 0 && Math.random() < 0.70) {
      finalDmg = Math.max(1, finalDmg - damageBlock);
      spawnFloatingText(p.x, p.y - 20, `🛡️ БЛОК -${damageBlock} (АВАНГАРД)`, "#94a3b8");
    }

    // 4. Passive Item: Blade Mail Damage Return (Reflect 35% damage back to boss)
    const reflectPct = stats.reflect || 0;
    if (reflectPct > 0) {
      const reflectDmg = Math.max(1, Math.floor(rawDmg * (reflectPct / 100)));
      if (ARENA.isRaidBossBattle && ARENA.bossEntity && ARENA.bossEntity.hp > 0) {
        applyDamageToBoss(ARENA.bossEntity, reflectDmg);
        spawnFloatingText(ARENA.bossEntity.x, ARENA.bossEntity.y - 25, `🪞 ВОЗВРАТКА -${reflectDmg}!`, "#c084fc");
      } else if (ARENA.creeps && ARENA.creeps.length > 0) {
        const targetCreep = ARENA.creeps.find(c => c.hp > 0);
        if (targetCreep) {
          safeDamageCreep(targetCreep, reflectDmg);
          spawnFloatingText(targetCreep.x, targetCreep.y - 25, `🪞 ВОЗВРАТКА -${reflectDmg}!`, "#c084fc");
        }
      }
    }

    const pMax = Math.max(100, p.maxHp || 500);

    // HEALTH GATE PROTECTION:
    // Only saves player ONCE per 60s from an unexpected lethal hit if they were at high health (>60% HP)
    // Prevents cheap 1-frame deaths from full HP, but consecutive hits WILL KILL!
    const nowFrame = ARENA.frameCount || 0;
    if (p.currentHp > pMax * 0.60 && finalDmg >= p.currentHp && (!p._lastHealthGateFrame || nowFrame - p._lastHealthGateFrame > 3600)) {
      p._lastHealthGateFrame = nowFrame;
      finalDmg = Math.max(1, p.currentHp - 1);
      p.currentHp = 1;
      p.isInvulnerable = 18; // Brief 0.3s window to react
      spawnFloatingText(p.x, p.y - 30, "🛡️ СПАСЕНИЕ ОТ ВАНШОТА!", "#38bdf8");
      triggerHaptic("heavy");
      return finalDmg;
    }

    p.currentHp = Math.max(0, p.currentHp - finalDmg);
    if (p.currentHp <= 0) {
      handlePlayerArenaDeath();
    }
    return finalDmg;
  }

  function setupArenaListeners(canvas) {
    function handleCanvasTap(cx, cy) {
      if (ARENA.waveState === "boss_victory") {
        if (RPG_STATE.lastBossChestReward) {
          openChestModal(RPG_STATE.lastBossChestReward);
        } else {
          ARENA.isRaidBossBattle = false;
          RPG_STATE.activeTab = "coop";
          renderRoot();
        }
        return;
      }
      if (ARENA.fallingChest && ARENA.fallingChest.landed && !ARENA.fallingChest.opened) {
        const fc = ARENA.fallingChest;
        if (Math.hypot(cx - fc.x, cy - fc.y) < 65) {
          fc.opened = true;
          if (RPG_STATE.lastBossChestReward) {
            openChestModal(RPG_STATE.lastBossChestReward);
          }
          return;
        }
      }
      if (ARENA.waveState === "boss_defeat") {
        if (ARENA._bossDefeatRetryBounds) {
          const rb = ARENA._bossDefeatRetryBounds;
          if (cx >= rb.x && cx <= rb.x + rb.w && cy >= rb.y && cy <= rb.y + rb.h) {
            if (ARENA.currentRaidBoss && ARENA.currentRaidBoss.id) {
              startRaidBossActionBattle(ARENA.currentRaidBoss.id);
            } else {
              exitRaidBossBattle();
            }
            return;
          }
        }
        if (ARENA._bossDefeatExitBounds) {
          const eb = ARENA._bossDefeatExitBounds;
          if (cx >= eb.x && cx <= eb.x + eb.w && cy >= eb.y && cy <= eb.y + eb.h) {
            exitRaidBossBattle();
            return;
          }
        }
        return;
      }
      if (ARENA.waveState === "prompt" || ARENA.waveState === "retry_prompt") {
        if (ARENA.waveState === "retry_prompt") {
          retryCurrentFloor();
        } else {
          if (ARENA._promptDisableBtnBounds) {
            const db = ARENA._promptDisableBtnBounds;
            if (cx >= db.x && cx <= db.x + db.w && cy >= db.y && cy <= db.y + db.h) {
              if (window.RPG && window.RPG.toggleArenaWaveConfirm) {
                if (!ARENA.autoAdvanceWaves) {
                  window.RPG.toggleArenaWaveConfirm();
                } else {
                  confirmNextWave();
                }
                return;
              }
            }
          }
          confirmNextWave();
        }
        return;
      }
      if (ARENA.isBossActive && ARENA._partyBtnBounds) {
        const pb = ARENA._partyBtnBounds;
        if (cx >= pb.x && cx <= pb.x + pb.w && cy >= pb.y && cy <= pb.y + pb.h) {
          window.RPG.toggleBossPartyMode();
          return;
        }
      }
      if (ARENA.blockWindowActive) {
        playerBlock();
        return;
      }
      if (ARENA.qteActive) {
        hitQTE();
        return;
      }
      if (ARENA.waveState === "fighting") {
        if (ARENA.topDownMode || ARENA.isRaidBossBattle) {
          fireTopDownAttack({ cx, cy });
        } else {
          playerSlashAttack();
        }
      }
    }

    function getEventArenaCoords(clientX, clientY) {
      const rect = canvas.getBoundingClientRect();
      if (ARENA.topDownMode || ARENA.isRaidBossBattle) {
        const clientW = rect.width || canvas.clientWidth || 360;
        const clientH = rect.height || canvas.clientHeight || 520;
        const zoom = Math.min(clientW / 520, clientH / 720);
        const offX = (clientW - 520 * zoom) / 2;
        const offY = (clientH - 720 * zoom) / 2;
        return {
          cx: Math.max(0, Math.min(520, (clientX - rect.left - offX) / zoom)),
          cy: Math.max(0, Math.min(720, (clientY - rect.top - offY) / zoom))
        };
      }
      return {
        cx: (clientX - rect.left) * (ARENA.width / (rect.width || 360)),
        cy: (clientY - rect.top) * (ARENA.height / (rect.height || 320))
      };
    }

    canvas.onclick = (e) => {
      const { cx, cy } = getEventArenaCoords(e.clientX, e.clientY);
      handleCanvasTap(cx, cy);
    };

    canvas.ontouchstart = (e) => {
      e.preventDefault();
      const touch = e.changedTouches[0];
      const { cx, cy } = getEventArenaCoords(touch.clientX, touch.clientY);

      // Only in legacy side-scroller boss mode, bottom 40% moves left/right
      if (!ARENA.topDownMode && !ARENA.isRaidBossBattle && ARENA.bossArenaMode && ARENA.waveState === "fighting" && cy > ARENA.height * 0.55) {
        ARENA._touchMoveId = touch.identifier;
        ARENA.moveInput.left = cx < ARENA.width * 0.38;
        ARENA.moveInput.right = cx > ARENA.width * 0.62;
        if (!ARENA.moveInput.left && !ARENA.moveInput.right) {
          playerSlashAttack();
        }
        return;
      }

      handleCanvasTap(cx, cy);
    };

    // Boss arena movement: touchmove for continuous direction
    canvas.ontouchmove = (e) => {
      e.preventDefault();
      if (!ARENA.bossArenaMode || !ARENA._touchMoveId) return;
      const touch = Array.from(e.changedTouches).find(t => t.identifier === ARENA._touchMoveId);
      if (!touch) return;
      const rect = canvas.getBoundingClientRect();
      const cx = (touch.clientX - rect.left) * (ARENA.width / rect.width);
      ARENA.moveInput.left = cx < ARENA.width * 0.38;
      ARENA.moveInput.right = cx > ARENA.width * 0.62;
    };

    canvas.ontouchend = (e) => {
      e.preventDefault();
      if (ARENA.bossArenaMode) {
        const touch = Array.from(e.changedTouches).find(t => t.identifier === ARENA._touchMoveId);
        if (touch) {
          ARENA.moveInput.left = false;
          ARENA.moveInput.right = false;
          ARENA._touchMoveId = null;
        }
      }
    };

    window.onkeyup = (e) => {
      const k = e.key.toLowerCase();
      if (ARENA.keysPressed) {
        delete ARENA.keysPressed[k];
        if (ARENA.topDownMode || ARENA.isRaidBossBattle) {
          let kx = 0, ky = 0;
          if (ARENA.keysPressed["w"] || ARENA.keysPressed["arrowup"]) ky -= 1;
          if (ARENA.keysPressed["s"] || ARENA.keysPressed["arrowdown"]) ky += 1;
          if (ARENA.keysPressed["a"] || ARENA.keysPressed["arrowleft"]) kx -= 1;
          if (ARENA.keysPressed["d"] || ARENA.keysPressed["arrowright"]) kx += 1;
          const kmag = Math.hypot(kx, ky);
          if (kmag > 0) {
            ARENA.joystick.dx = kx / kmag;
            ARENA.joystick.dy = ky / kmag;
            ARENA.player.isMoving = true;
            ARENA.player.facingAngle = Math.atan2(ky, kx);
          } else {
            ARENA.joystick.dx = 0;
            ARENA.joystick.dy = 0;
            ARENA.player.isMoving = false;
          }
        }
      }
      if (!ARENA.bossArenaMode) return;
      if (k === "a" || k === "arrowleft") ARENA.moveInput.left = false;
      if (k === "d" || k === "arrowright") ARENA.moveInput.right = false;
    };

    window.onkeydown = (e) => {
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable)) return;
      if (RPG_STATE.activeTab !== "farm" || RPG_STATE.farmMode !== "arena") return;
      const k = e.key.toLowerCase();

      // WASD / Arrow keys for Top-Down free movement
      if (ARENA.topDownMode || ARENA.isRaidBossBattle) {
        if (!ARENA.keysPressed) ARENA.keysPressed = {};
        if (["w", "arrowup", "s", "arrowdown", "a", "arrowleft", "d", "arrowright"].includes(k)) {
          ARENA.keysPressed[k] = true;
          let kx = 0, ky = 0;
          if (ARENA.keysPressed["w"] || ARENA.keysPressed["arrowup"]) ky -= 1;
          if (ARENA.keysPressed["s"] || ARENA.keysPressed["arrowdown"]) ky += 1;
          if (ARENA.keysPressed["a"] || ARENA.keysPressed["arrowleft"]) kx -= 1;
          if (ARENA.keysPressed["d"] || ARENA.keysPressed["arrowright"]) kx += 1;

          const kmag = Math.hypot(kx, ky);
          if (kmag > 0) {
            ARENA.joystick.dx = kx / kmag;
            ARENA.joystick.dy = ky / kmag;
            ARENA.joystick.power = 1.0;
            ARENA.player.isMoving = true;
            ARENA.player.facingAngle = Math.atan2(ky, kx);
          } else {
            ARENA.joystick.dx = 0;
            ARENA.joystick.dy = 0;
            ARENA.player.isMoving = false;
          }
          e.preventDefault();
          return;
        }
        if (k === "shift" || k === "c") {
          playerPerformDashRoll();
          e.preventDefault();
          return;
        }
      }
      // Boss Arena Movement (A/D or Arrows)
      if (ARENA.bossArenaMode) {
        if (k === "a" || k === "arrowleft") { ARENA.moveInput.left = true; e.preventDefault(); return; }
        if (k === "d" || k === "arrowright") { ARENA.moveInput.right = true; e.preventDefault(); return; }
        if (k === "shift" || k === "c") { playerBossArenaDodge(); e.preventDefault(); return; }
      }
      if (k === " " || k === "spacebar" || k === "enter") {
        e.preventDefault();
        if (ARENA.waveState === "prompt") {
          confirmNextWave();
        } else if (ARENA.waveState === "retry_prompt") {
          retryCurrentFloor();
        } else if (ARENA.waveState === "boss_defeat") {
          if (ARENA.currentRaidBoss && ARENA.currentRaidBoss.id) {
            startRaidBossActionBattle(ARENA.currentRaidBoss.id);
          } else {
            exitRaidBossBattle();
          }
        } else if (ARENA.blockWindowActive) {
          playerBlock();
        } else if (ARENA.qteActive) {
          hitQTE();
        } else {
          playerSlashAttack();
        }
      } else if (k === "e") {
        castPlayerSkill1();
      } else if (k === "q") {
        castPlayerUltimate();
      } else if (k === "f") {
        usePlayerPotion();
      } else if (k === "r" || k === "1") {
        useActiveItemAction(0);
      } else if (k === "t" || k === "2") {
        useActiveItemAction(1);
      } else if (k === "shift" || k === "c") {
        playerPerformDash();
      } else if (k === "b") {
        playerBlock();
      }
    };
  }

  function startArenaLoop() {
    stopArenaLoop();
    if (ARENA.startLoopTimeout) {
      cancelAnimationFrame(ARENA.startLoopTimeout);
      clearTimeout(ARENA.startLoopTimeout);
      ARENA.startLoopTimeout = null;
    }
    const canvas = document.getElementById("rpg-action-canvas");
    if (canvas) {
      const r = canvas.getBoundingClientRect();
      const hasSize = (r.width > 50) || (canvas.clientWidth > 50);
      if (!hasSize) {
        // Canvas not laid out yet — retry on next frame
        ARENA.startLoopTimeout = requestAnimationFrame(() => startArenaLoop());
        return;
      }
      if (!ARENA.isRaidBossBattle || !ARENA.bossEntity) {
        initArenaCanvas();
      } else if (!ARENA.ctx || ARENA.canvas !== canvas) {
        bindArenaCanvas(canvas);
      }
    }
    ARENA.running = true;
    function loop() {
      if (!ARENA.running) return;
      try {
        updateArena();
        renderArena();
      } catch (err) {
        console.error("Arena animation frame error:", err);
      }
      if (ARENA.running) {
        ARENA.animId = requestAnimationFrame(loop);
      }
    }
    ARENA.animId = requestAnimationFrame(loop);
  }

  function stopArenaLoop() {
    ARENA.running = false;
    if (ARENA.animId) {
      cancelAnimationFrame(ARENA.animId);
      ARENA.animId = null;
    }
    if (ARENA.startLoopTimeout) {
      cancelAnimationFrame(ARENA.startLoopTimeout);
      clearTimeout(ARENA.startLoopTimeout);
      ARENA.startLoopTimeout = null;
    }
  }

  // ---------------------------------------------------------------------------
  // MAIN GAME LOOP UPDATE
  // ---------------------------------------------------------------------------
