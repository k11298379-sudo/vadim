"""
NATBIRZHA Database Models Package.
All models inherit from Base and are automatically discovered by SQLAlchemy.
"""

from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.inventory import (
    CANONICAL_ITEMS,
    NatInventory,
    get_item_base_price,
    get_npc_buy_price,
    get_npc_sell_price
)
from backend.natbirzha.models.market import NatMarketOrder, NatMarketTrade
from backend.natbirzha.models.stocks import NatStock, NatStockHolding, NatStockOrder, NatDividend, NatDividendPayment
from backend.natbirzha.models.contracts import NatContract, NatLoan
from backend.natbirzha.models.military import NatArmy, NatTournament, NatTournamentParticipant
from backend.natbirzha.models.alliances import NatAlliance, NatAllianceMember
from backend.natbirzha.models.restructuring import NatRestructuring, NatDailyFinancials
from backend.natbirzha.models.idempotency import NatIdempotencyRecord
from backend.natbirzha.models.npc import NatNpcDailyVolume
from backend.natbirzha.models.premium import NatMilitaryUpgrade, NatPremiumLedgerEntry, NatPremiumLicense
from backend.natbirzha.models.season import NatSeasonResetOperation
from backend.natbirzha.models.combat import (
    NatArmyUnit,
    NatBattle,
    NatBattleSnapshot,
    NatMilitaryRatingEvent,
    NatPveCorporation,
    NatPveVictory,
    NatPvpCooldown,
)
from backend.natbirzha.models.instruments import (
    NatInstrumentPosition,
    NatInstrumentTrade,
    NatReferenceRateSnapshot,
)
from backend.natbirzha.models.creator import (
    NatStateTreasury,
    NatCreatorAuditLog,
    NatMarketRestriction,
    NatMarketWarning,
    NatStateBond,
    NatStateBondHolding,
    NatBondSettlement,
    NatBondListing,
)

__all__ = [
    "NatCompany",
    "NatFactory",
    "CANONICAL_ITEMS",
    "NatInventory",
    "get_item_base_price",
    "get_npc_buy_price",
    "get_npc_sell_price",
    "NatMarketOrder",
    "NatMarketTrade",
    "NatStock",
    "NatStockHolding",
    "NatStockOrder",
    "NatDividend",
    "NatDividendPayment",
    "NatContract",
    "NatLoan",
    "NatArmy",
    "NatTournament",
    "NatTournamentParticipant",
    "NatAlliance",
    "NatAllianceMember",
    "NatRestructuring",
    "NatDailyFinancials",
    "NatIdempotencyRecord",
    "NatNpcDailyVolume",
    "NatPremiumLedgerEntry",
    "NatPremiumLicense",
    "NatMilitaryUpgrade",
    "NatSeasonResetOperation",
    "NatArmyUnit",
    "NatBattle",
    "NatBattleSnapshot",
    "NatMilitaryRatingEvent",
    "NatPveCorporation",
    "NatPveVictory",
    "NatPvpCooldown",
    "NatReferenceRateSnapshot",
    "NatInstrumentPosition",
    "NatInstrumentTrade",
    "NatStateTreasury",
    "NatCreatorAuditLog",
    "NatMarketRestriction",
    "NatMarketWarning",
    "NatStateBond",
    "NatStateBondHolding",
    "NatBondSettlement",
    "NatBondListing",
]
