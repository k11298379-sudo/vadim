"""PvE corporate-war transaction, reward, rating, and replay checks."""

import asyncio
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.db.models import Base
import backend.natbirzha.models  # noqa: F401
from backend.natbirzha.models.combat import NatArmyUnit, NatBattle, NatPveVictory
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.services.pve_service import PveService, PveWarError


async def run_async() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with sessions() as session:
        strong = NatCompany(
            user_id=930001,
            name="Strong Corp",
            specialization="technoprom",
            cash=50_000,
            territory_tiles=4,
            military_rating=1000,
        )
        weak = NatCompany(
            user_id=930002,
            name="Weak Corp",
            specialization="agrarian",
            cash=50_000,
            territory_tiles=4,
            military_rating=1000,
        )
        session.add_all([strong, weak])
        await session.flush()
        session.add_all(
            [
                NatArmyUnit(company_id=strong.id, unit_type="infantry", quantity=500),
                NatArmyUnit(company_id=strong.id, unit_type="tanks", quantity=10),
                NatArmyUnit(company_id=weak.id, unit_type="infantry", quantity=1),
            ]
        )
        await session.commit()

        targets = await PveService.list_targets(session, strong)
        assert len(targets) == 12
        assert [row["tier"] for row in targets].count(1) == 3
        assert any(row["available"] is False for row in targets)
        assert all(row["strength_range"]["min"] < row["strength_range"]["max"] for row in targets)
        scout = await PveService.scout_target(session, strong, "local_logistics")
        assert scout["accuracy"] == "estimated" and scout["known_units"] is None
        assert scout["risk"] in {"low", "medium", "high", "extreme"}
        assert set(scout["expected_losses"]) == {
            "infantry", "border_guards", "tanks", "drones", "aircraft", "air_defense"
        }
        assert all(row["min"] <= row["max"] for row in scout["expected_losses"].values())

        before_cash = strong.cash
        before_territory = strong.territory_tiles
        victory = await PveService.attack_target(
            session,
            strong,
            "local_logistics",
            "pve:strong:1",
            now=datetime(2026, 9, 18, 12, 0, 0),
        )
        assert victory["winner"] == "attacker"
        assert victory["territory_awarded"] == 1
        assert strong.territory_tiles == before_territory + 1
        assert strong.cash > before_cash
        assert strong.military_rating > 1000
        territory_after = strong.territory_tiles
        cash_after = strong.cash
        rating_after = strong.military_rating

        replay = await PveService.attack_target(
            session,
            strong,
            "local_logistics",
            "pve:strong:1",
            now=datetime(2026, 9, 18, 12, 1, 0),
        )
        assert replay == victory
        assert (strong.territory_tiles, strong.cash, strong.military_rating) == (
            territory_after,
            cash_after,
            rating_after,
        )

        try:
            await PveService.attack_target(
                session,
                strong,
                "local_logistics",
                "pve:strong:2",
                now=datetime(2026, 9, 18, 12, 2, 0),
            )
        except PveWarError as exc:
            assert exc.reason == "already_conquered"
        else:
            raise AssertionError("A PvE corporation cannot award territory twice")

        defeat = await PveService.attack_target(
            session,
            weak,
            "local_logistics",
            "pve:weak:1",
            now=datetime(2026, 9, 18, 13, 0, 0),
        )
        assert defeat["winner"] == "defender"
        assert defeat["territory_awarded"] == 0
        assert weak.territory_tiles == 4
        assert weak.military_rating < 1000
        await session.commit()

        battle_count = await session.scalar(select(func.count()).select_from(NatBattle))
        victory_count = await session.scalar(select(func.count()).select_from(NatPveVictory))
        assert battle_count == 2
        assert victory_count == 1

    await engine.dispose()
    print("NATBIRZHA PvE corporate-war checks: PASS")


if __name__ == "__main__":
    asyncio.run(run_async())
