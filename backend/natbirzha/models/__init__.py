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
from backend.natbirzha.models.stocks import NatStock, NatStockHolding, NatStockOrder, NatDividend
from backend.natbirzha.models.contracts import NatContract, NatLoan
from backend.natbirzha.models.military import NatArmy, NatTournament, NatTournamentParticipant
from backend.natbirzha.models.alliances import NatAlliance, NatAllianceMember
from backend.natbirzha.models.restructuring import NatRestructuring, NatDailyFinancials
from backend.natbirzha.models.idempotency import NatIdempotencyRecord
from backend.natbirzha.models.creator import (
    NatStateTreasury,
    NatCreatorAuditLog,
    NatMarketRestriction,
    NatMarketWarning,
    NatStateBond
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
    "NatStateTreasury",
    "NatCreatorAuditLog",
    "NatMarketRestriction",
    "NatMarketWarning",
    "NatStateBond",
]
