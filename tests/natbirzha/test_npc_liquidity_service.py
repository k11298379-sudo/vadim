import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import select

from backend.db.models import Base
from backend.db.session import async_session_factory, engine
from backend.natbirzha.config import nat_settings
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.inventory import NatInventory
from backend.natbirzha.models.npc import NatNpcDailyVolume
from backend.natbirzha.services.company_service import CompanyService
from backend.natbirzha.services.npc_service import NPCReserveService


async def run_checks():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        company = await CompanyService.create_company(session, 910001, "NPC Test One", "miner")
        assert await NPCReserveService.get_active_player_scaling_factor(session) == 1.0

        # Failed trades must not consume daily NPC quota.
        company.cash = 0.0
        failed = await NPCReserveService.execute_npc_trade(session, company, "iron_ore", "BUY", 5.0)
        assert failed["reason"] == "insufficient_cash"
        usage = (await session.execute(select(NatNpcDailyVolume))).scalars().all()
        assert usage == []

        company.cash = 100000.0
        ok = await NPCReserveService.execute_npc_trade(session, company, "iron_ore", "BUY", 5.0)
        assert ok["success"] is True
        assert ok["npc_scaling_factor"] == 1.0
        await session.commit()

        # Populate to threshold counts and verify required 1/5/20/30 scaling steps.
        for idx in range(2, 31):
            await CompanyService.create_company(
                session, 910000 + idx, f"NPC Scale {idx}", "forester"
            )
            if idx == 5:
                assert await NPCReserveService.get_active_player_scaling_factor(session) == 0.8
            if idx == 20:
                assert await NPCReserveService.get_active_player_scaling_factor(session) == 0.3
            if idx == 30:
                assert await NPCReserveService.get_active_player_scaling_factor(session) == 0.1

        # At 30 players the per-item daily quota is 10% of the base quota.
        quota = await NPCReserveService.get_daily_quota(session)
        assert quota["daily_quota_per_item"] == round(
            nat_settings.NPC_BASE_DAILY_VOLUME_PER_ITEM * 0.1, 2
        )

        # Premium raw materials are never unlimited NPC supply.  The market may
        # still trade them P2P, but the state reserve exposes only a tiny,
        # item-specific daily emergency reserve when a player buys from NPC.
        rare_quota = await NPCReserveService.get_daily_quota(session, "lithium_raw", "BUY")
        assert rare_quota["daily_quota_per_item"] == nat_settings.NPC_RARE_SELL_RESERVES["lithium_raw"]
        company.cash = 100000.0
        rare_ok = await NPCReserveService.execute_npc_trade(session, company, "lithium_raw", "BUY", rare_quota["daily_quota_per_item"])
        assert rare_ok["success"] is True and rare_ok["remaining_npc_quota"] == 0.0
        rare_blocked = await NPCReserveService.execute_npc_trade(session, company, "lithium_raw", "BUY", 0.01)
        assert rare_blocked["success"] is False and rare_blocked["reason"] == "npc_volume_limit"

        # Inventory overflow is rejected before quota consumption.
        inv = (await session.execute(
            select(NatInventory).where(
                NatInventory.company_id == company.id,
                NatInventory.item_id == "iron_ore",
            )
        )).scalar_one()
        inv.quantity = nat_settings.INVENTORY_MAX_QUANTITY_PER_ITEM
        await session.flush()
        overflow = await NPCReserveService.execute_npc_trade(
            session, company, "iron_ore", "BUY", 1.0
        )
        assert overflow["reason"] == "inventory_overflow"

    print("NPC LIQUIDITY SERVICE: ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(run_checks())
