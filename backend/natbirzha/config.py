import os
from datetime import datetime, date, time
import zoneinfo
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class NatbirzhaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GAME_TIMEZONE: str = Field(default="Asia/Yekaterinburg", description="Timezone for calendar settlements")
    ALLOW_TEST_AUTH: bool = Field(default=True, description="Allow test HMAC signature tokens in local dev/tests")
    TEST_AUTH_SECRET: str = Field(default="natbirzha_test_secret_key_2026", description="Secret for signing test initData")
    BETA_TESTERS_ONLY: bool = Field(default=True, description="Restrict Natbirzha access to beta-testers and admins only")

    # Specialization efficiency limits (strict)
    OWN_SPEC_EFFICIENCY: float = 1.00       # 100%
    FOREIGN_SPEC_EFFICIENCY: float = 0.10   # 10%
    FOREIGN_LICENSED_MAX: float = 0.12      # Max 12% with special license
    FOREIGN_LICENSE_COST_NAT: int = 50      # NAT sink: purchase foreign spec license
    RESPEC_COOLDOWN_DAYS: int = 7
    RESPEC_COST_PCT: float = 0.25

    # NPC State Reserve (Госрезерв) multipliers
    NPC_BUY_FLOOR_MULT: float = 0.80        # NPC buys surplus at 80% base price
    NPC_SELL_CAP_MULT: float = 1.25         # NPC sells supplies at 125% base price
    NPC_VOLUME_SCALING_FACTORS: Dict[int, float] = {
        1: 1.0,   # 1 player: 100% NPC volume quota
        5: 0.8,   # 5 players: 80% NPC quota
        20: 0.3,  # 20 players: 30% NPC quota
        30: 0.1   # 30 players: 10% NPC quota
    }

    # Alliance rules
    ALLIANCE_MAX_MEMBERS: int = 3           # Strictly maximum 3 members

    # Tournament rules
    TOURNAMENT_CYCLE_HOURS: int = 72        # 72h tournament cycle
    TOURNAMENT_SNAPSHOT_MINUTES: int = 15   # Immutable snapshot before finish
    TOURNAMENT_WINNER_PRIZE_NAT: int = 100  # 100 NAT to 1st place

    # IPO rules
    IPO_MIN_LEVEL: int = 2
    IPO_MIN_SHARES: int = 10000
    IPO_FOUNDER_MIN_PCT: float = 0.60       # Founder retains at least 60%
    IPO_FLOAT_MAX_PCT: float = 0.40         # Public float at most 40%
    IPO_SPO_COOLDOWN_DAYS: int = 14
    IPO_NAV_WEIGHT: float = 1.0
    IPO_PROFIT_PE_MULT: float = 8.0
    IPO_CASH_DISCOUNT: float = 0.85
    IPO_REQUIRE_FINANCIAL_HISTORY: bool = False  # Configurable IPO eligibility rule

    # Dividends
    DIVIDEND_POOL_PCT: float = 0.10         # 10% of closed daily distributable profit

    # Bankruptcy & Restructuring
    BANKRUPTCY_LIQUIDATION_POOL_PCT: float = 0.40  # 40% of audited NAV at snapshot
    BANKRUPTCY_FEE_CALENDAR_DAYS: int = 2          # Next 2 real calendar dates in GAME_TIMEZONE
    BANKRUPTCY_FEE_RATE: float = 0.30              # 30% of positive daily profit

    # Base Economic Constants
    STARTING_CASH: float = 50000.0
    STARTING_TERRITORY_TILES: int = 4
    BASE_MUNICIPAL_ENERGY_TICK: float = 10.0       # Free 10.0 MWh/tick breaking energy cycle

    # Factory Construction Costs
    FACTORY_BASE_COSTS: Dict[str, float] = {
        "smelter": 5000.0,
        "aluminum_plant": 8000.0,
        "hydro_solar": 6000.0,
        "thermal_plant": 6000.0,
        "nuclear_plant": 25000.0,
        "oil_rig": 5500.0,
        "refinery": 7000.0,
        "chem_plant": 5500.0,
        "polymer_plant": 8500.0,
        "mine": 5000.0,
        "deep_mine": 9000.0,
        "uranium_quarry": 15000.0,
        "logging_camp": 5000.0,
        "sawmill": 6500.0,
        "farm": 5000.0,
        "food_factory": 7000.0,
        "machinery_plant": 7500.0,
        "electronics_fab": 8000.0,
        "centrifuge": 18000.0,
        "defense_plant": 30000.0,
    }

    def get_factory_cost(self, factory_type: str, existing_count: int = 0) -> float:
        base = self.FACTORY_BASE_COSTS.get(factory_type, 5000.0)
        return round(base * (1.0 + 0.15 * existing_count), 2)

nat_settings = NatbirzhaSettings()

def get_game_tz() -> zoneinfo.ZoneInfo:
    try:
        return zoneinfo.ZoneInfo(nat_settings.GAME_TIMEZONE)
    except Exception:
        return zoneinfo.ZoneInfo("UTC")

def normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normalizes any datetime to offset-naive game time in GAME_TIMEZONE.
    Guarantees that datetime subtractions and comparisons never crash with
    TypeError: can't subtract/compare offset-naive and offset-aware datetimes.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(get_game_tz()).replace(tzinfo=None)
    return dt

def get_game_now() -> datetime:
    """Returns current game timestamp normalized as offset-naive game timezone."""
    return datetime.now(get_game_tz()).replace(tzinfo=None)

def get_game_today() -> date:
    return datetime.now(get_game_tz()).date()

