/**
 * Natbirzha - Canonical Items Registry and Localization Dictionary
 * Maps item IDs to Russian names, emojis, and measurement units.
 */

export const ITEMS = {
  // Tier 0: Utilities & Naturals
  grid_quota: { name: 'Квота энергосети', icon: '⚡', unit: 'МВт·ч' },
  energy: { name: 'Электроэнергия', icon: '💡', unit: 'МВт·ч' },
  water: { name: 'Техническая вода', icon: '💧', unit: 'м³' },
  well_lease: { name: 'Отвод скважины', icon: '📜', unit: 'шт.' },
  forest_fund: { name: 'Квота лесного фонда', icon: '🌲', unit: 'га' },

  // Tier 1: Primary Extraction
  grain: { name: 'Зерно', icon: '🌾', unit: 'т' },
  bio_raw: { name: 'Биосырьё', icon: '🌱', unit: 'т' },
  wood_raw: { name: 'Кругляк древесины', icon: '🪵', unit: 'м³' },
  coal: { name: 'Каменный уголь', icon: '🪨', unit: 'т' },
  iron_ore: { name: 'Железная руда', icon: '⛏️', unit: 'т' },
  bauxite: { name: 'Бокситы', icon: '🧱', unit: 'т' },
  minerals: { name: 'Минералы и флюс', icon: '💎', unit: 'т' },
  oil_crude: { name: 'Сырая нефть', icon: '🛢️', unit: 'барр.' },
  gas_natural: { name: 'Природный газ', icon: '🔥', unit: 'тыс. м³' },
  rare_earths: { name: 'Редкоземельные металлы', icon: '✨', unit: 'кг' },
  lithium_raw: { name: 'Неочищенный литий', icon: '🔋', unit: 'т' },
  uranium_raw: { name: 'Урановая руда', icon: '☢️', unit: 'т' },

  // Tier 2: Intermediate Processing
  steel: { name: 'Конструкционная сталь', icon: '🔩', unit: 'т' },
  aluminum: { name: 'Алюминий', icon: '🪙', unit: 'т' },
  lumber: { name: 'Пиломатериалы', icon: '🪵', unit: 'м³' },
  cellulose: { name: 'Целлюлоза', icon: '📄', unit: 'т' },
  food: { name: 'Продовольственные пайки', icon: '🥫', unit: 'ящ.' },
  fuel_diesel: { name: 'Дизельное топливо', icon: '⛽', unit: 'л' },
  basic_chem: { name: 'Базовые реагенты', icon: '🧪', unit: 'т' },
  fertilizer: { name: 'Удобрения', icon: '🌱', unit: 'т' },

  // Tier 3: Advanced & High-Tech
  plastics: { name: 'Полимеры', icon: '🧪', unit: 'т' },
  catalyst: { name: 'Катализаторы', icon: '💠', unit: 'кг' },
  lithium_pure: { name: 'Аккумуляторный литий', icon: '🔋', unit: 'кг' },
  uranium_enriched: { name: 'Обогащённый уран', icon: '⚛️', unit: 'шт.' },
  machinery: { name: 'Механические узлы', icon: '⚙️', unit: 'шт.' },
  electronics: { name: 'Электронные чипы', icon: '💻', unit: 'шт.' },
  batteries: { name: 'Тяговые батареи', icon: '🔋', unit: 'шт.' },

  // Tier 4: Military
  military_gear: { name: 'Военное снаряжение', icon: '🪖', unit: 'компл.' },
};

/**
 * Returns localized metadata for a given item ID with safe fallbacks.
 * @param {string} itemId
 * @returns {{ name: string, icon: string, unit: string }}
 */
export function getItemInfo(itemId) {
  if (!itemId) return { name: 'Неизвестно', icon: '📦', unit: 'шт.' };
  const key = String(itemId).toLowerCase().trim();
  return ITEMS[key] || {
    name: key.replace(/_/g, ' '),
    icon: '📦',
    unit: 'шт.'
  };
}