import { NatAPI } from '../api.js';
import { store } from '../state.js';

const UNITS = [
  { id: 'infantry', name: 'Пехотный взвод', cost: 100, steel: 1, power: 5, icon: '🪖' },
  { id: 'heavy_tank', name: 'Тяжёлый танк', cost: 500, steel: 5, power: 30, icon: '🛡️' },
];

export async function renderMilitary(container, showToast) {
  let militaryData = null;
  let tournamentData = null;

  try {
    militaryData = await NatAPI.getMilitaryStatus();
  } catch (err) {
    console.error('Military status error:', err);
  }

  try {
    tournamentData = await NatAPI.getCurrentTournament();
  } catch (err) {
    console.error('Tournament fetch error:', err);
  }

  const army = militaryData?.army || { infantry: 0, tanks: 0, combat_power: 0 };
  const participants = tournamentData?.participants || [];

  container.innerHTML = `
    <div class="space-y-4 max-w-md mx-auto p-4 pb-24">
      <div>
        <h2 class="text-xl font-black text-slate-900 dark:text-white">Оборонный Комплекс</h2>
        <p class="text-xs text-slate-500">Военные подразделения, альянсы и 72-часовые турниры</p>
      </div>

      <!-- 72h Tournament Card -->
      <div class="glass-card rounded-2xl p-4 shadow-sm border-l-4 border-l-amber-500 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xl">🏆</span>
            <div>
              <div class="text-xs font-bold text-slate-900 dark:text-white">Сезонный Турнир 11 «Б»</div>
              <div class="text-[10px] text-slate-400">72-часовой цикл • Тайбрейк: ранний захват</div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-[10px] uppercase font-bold text-amber-500">Призовой фонд</div>
            <div class="text-sm font-black font-mono text-amber-500">100 NAT</div>
          </div>
        </div>

        <div class="space-y-1.5 pt-2 border-t border-slate-200 dark:border-slate-800">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Лидерборд турнира:</div>
          ${participants.length === 0 ? `
            <div class="text-slate-400 text-xs py-2 text-center">Участников пока нет</div>
          ` : participants.map((p, idx) => `
            <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-xs font-mono">
              <div class="flex items-center gap-2">
                <span class="font-bold ${idx === 0 ? 'text-amber-500' : 'text-slate-400'}">#${idx + 1}</span>
                <span class="font-bold text-slate-800 dark:text-white">${p.company_name}</span>
              </div>
              <span class="text-blue-500 font-bold">${p.score} очков</span>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Army Status Card -->
      <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Состояние ваших вооружённых сил</h3>
          <span class="text-xs font-mono font-bold text-emerald-500">${army.combat_power || 0} Боевая мощь</span>
        </div>

        <div class="grid grid-cols-2 gap-2">
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
            <div class="text-lg">🪖</div>
            <div class="text-[11px] text-slate-400 mt-1">Пехота</div>
            <div class="text-base font-black font-mono text-slate-900 dark:text-white">${army.infantry || 0}</div>
          </div>

          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
            <div class="text-lg">🛡️</div>
            <div class="text-[11px] text-slate-400 mt-1">Танки</div>
            <div class="text-base font-black font-mono text-slate-900 dark:text-white">${army.tanks || 0}</div>
          </div>
        </div>
      </div>

      <!-- Recruit Units Card -->
      <div class="glass-card rounded-2xl p-4 shadow-sm space-y-3">
        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Формирование подразделений</h3>
        <div class="space-y-2">
          ${UNITS.map(u => `
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-2xl">${u.icon}</span>
                <div>
                  <div class="text-xs font-bold text-slate-900 dark:text-white">${u.name}</div>
                  <div class="text-[10px] text-slate-400 font-mono">${u.cost} cash + ${u.steel}т стали (${u.power} мощи)</div>
                </div>
              </div>
              <button
                class="recruit-unit-btn px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs active:scale-95 transition-all"
                data-unit-id="${u.id}"
                data-name="${u.name}"
              >
                Нанять
              </button>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // Recruit button listeners
  container.querySelectorAll('.recruit-unit-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const unitId = btn.getAttribute('data-unit-id');
      const unitName = btn.getAttribute('data-name');
      const countStr = prompt(`Сколько единиц [${unitName}] нанять?`, '1');
      const count = parseInt(countStr, 10);
      if (!count || count <= 0) return;

      try {
        btn.disabled = true;
        await NatAPI.recruitUnits(unitId, count);
        showToast(`Успешно нанято: ${count} ед. [${unitName}]`, 'success');
        const refreshed = await NatAPI.getMyCompany();
        store.setCompany(refreshed);
        renderMilitary(container, showToast);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btn.disabled = false;
      }
    });
  });
}
