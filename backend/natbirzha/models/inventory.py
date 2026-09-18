from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Integer, String, Float, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.models import Base
from backend.natbirzha.config import nat_settings

# Canonical registry of all 33 game items (Single Source of Truth)
CANONICAL_ITEMS: Dict[str, Dict[str, Any]] = {
    # Tier 0: Utilities & Naturals
    "grid_quota": {"name": "Лимит энергосети", "category": "utility", "unit": "МВт·ч", "base_price": 5.0},
    "energy": {"name": "Электроэнергия", "category": "utility", "unit": "МВт·ч", "base_price": 10.0},
    "water": {"name": "Техническая вода", "category": "utility", "unit": "м³", "base_price": 2.0},
    "well_lease": {"name": "Отвод скважины", "category": "asset", "unit": "шт.", "base_price": 1000.0},
    "forest_fund": {"name": "Квота лесного фонда", "category": "asset", "unit": "га", "base_price": 800.0},

    # Tier 1: Primary Extraction
    "grain": {"name": "Зерно", "category": "raw", "unit": "т", "base_price": 20.0},
    "bio_raw": {"name": "Биосырье", "category": "raw", "unit": "т", "base_price": 18.0},
    "wood_raw": {"name": "Кругляк древесины", "category": "raw", "unit": "м³", "base_price": 25.0},
    "coal": {"name": "Каменный уголь", "category": "raw", "unit": "т", "base_price": 30.0},
    "iron_ore": {"name": "Железная руда", "category": "raw", "unit": "т", "base_price": 35.0},
    "bauxite": {"name": "Бокситы", "category": "raw", "unit": "т", "base_price": 40.0},
    "minerals": {"name": "Минералы и флюс", "category": "raw", "unit": "т", "base_price": 22.0},
    "oil_crude": {"name": "Сырая нефть", "category": "raw", "unit": "барр.", "base_price": 50.0},
    "gas_natural": {"name": "Природный газ", "category": "raw", "unit": "тыс. м³", "base_price": 45.0},
    "rare_earths": {"name": "Редкоземельные металлы", "category": "raw", "unit": "кг", "base_price": 120.0},
    "lithium_raw": {"name": "Неочищенный литий", "category": "raw", "unit": "т", "base_price": 85.0},
    "uranium_raw": {"name": "Урановая руда", "category": "raw", "unit": "т", "base_price": 200.0},

    # Tier 2: Intermediate Processing
    "steel": {"name": "Конструкционная сталь", "category": "intermediate", "unit": "т", "base_price": 90.0},
    "aluminum": {"name": "Алюминий первичный", "category": "intermediate", "unit": "т", "base_price": 110.0},
    "lumber": {"name": "Пиломатериалы", "category": "intermediate", "unit": "м³", "base_price": 55.0},
    "cellulose": {"name": "Целлюлоза", "category": "intermediate", "unit": "т", "base_price": 65.0},
    "food": {"name": "Продовольственные пайки", "category": "intermediate", "unit": "ящ.", "base_price": 45.0},
    "fuel_diesel": {"name": "Дизельное топливо", "category": "intermediate", "unit": "л", "base_price": 1.2},
    "basic_chem": {"name": "Базовые кислоты и реагенты", "category": "intermediate", "unit": "т", "base_price": 70.0},
    "fertilizer": {"name": "Удобрения", "category": "intermediate", "unit": "т", "base_price": 50.0},

    # Tier 3: Advanced & High-Tech
    "plastics": {"name": "Конструкционные полимеры", "category": "finished", "unit": "т", "base_price": 130.0},
    "catalyst": {"name": "Промышленные катализаторы", "category": "finished", "unit": "кг", "base_price": 250.0},
    "lithium_pure": {"name": "Аккумуляторный литий", "category": "finished", "unit": "кг", "base_price": 180.0},
    "uranium_enriched": {"name": "Обогащенный уран (ТВЭЛ)", "category": "finished", "unit": "шт.", "base_price": 600.0},
    "machinery": {"name": "Механические узлы и станки", "category": "finished", "unit": "шт.", "base_price": 320.0},
    "electronics": {"name": "Электронные чипы", "category": "finished", "unit": "шт.", "base_price": 400.0},
    "batteries": {"name": "Тяговые батареи", "category": "finished", "unit": "шт.", "base_price": 350.0},

    # Tier 4: Military
    "military_gear": {"name": "Военное снаряжение ВПК", "category": "military", "unit": "компл.", "base_price": 500.0},
}

def get_item_base_price(item_id: str) -> float:
    item = CANONICAL_ITEMS.get(item_id)
    if not item:
        raise ValueError(f"Unknown canonical item: {item_id}")
    return float(item["base_price"])

def get_npc_buy_price(item_id: str) -> float:
    return round(get_item_base_price(item_id) * nat_settings.NPC_BUY_FLOOR_MULT, 2)

def get_npc_sell_price(item_id: str) -> float:
    return round(get_item_base_price(item_id) * nat_settings.NPC_SELL_CAP_MULT, 2)


class NatInventory(Base):
    __tablename__ = "nat_inventory"
    __table_args__ = (
        UniqueConstraint("company_id", "item_id", name="uq_nat_inventory_company_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_cost_basis: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def available_quantity(self) -> float:
        return max(0.0, self.quantity - self.reserved_quantity)
