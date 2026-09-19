"""Explicit, idempotent seasonal reset preserves Telegram identities and creator grant."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.db.models import Base, User
import backend.natbirzha.models  # noqa: F401
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.season import NatSeasonResetOperation
from backend.natbirzha.services.season_reset_service import SeasonResetService


async def run_async() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with sessions() as session:
        creator = User(tg_id=991001, full_name="Creator", role="admin")
        player = User(tg_id=991002, full_name="Player")
        session.add_all([creator, player])
        await session.flush()
        old_creator = NatCompany(user_id=creator.id, name="Creator Corp", specialization="miner", cash=999)
        old_player = NatCompany(user_id=player.id, name="Player Corp", specialization="forester", cash=999)
        session.add_all([old_creator, old_player])
        await session.flush()
        session.add(NatFactory(company_id=old_player.id, building_type="sawmill", specialization="forester"))
        await session.commit()

        preview = await SeasonResetService.preview(session)
        assert preview["affected_companies"] == 2 and preview["creator_companies"] == 1
        result = await SeasonResetService.execute(
            session, operation_id="season-test-001", actor_tg_id=creator.tg_id, backup_reference="test-backup"
        )
        assert result["status"] == "completed" and result["affected_companies"] == 2
        companies = (await session.execute(select(NatCompany).order_by(NatCompany.name))).scalars().all()
        assert len(companies) == 2
        by_name = {company.name: company for company in companies}
        assert by_name["Creator Corp"].cash == 200_000
        assert by_name["Player Corp"].cash == 50_000
        assert by_name["Player Corp"].level == 1 and by_name["Player Corp"].territory_tiles == 4
        assert not (await session.execute(select(NatFactory))).scalars().all()
        replay = await SeasonResetService.execute(
            session, operation_id="season-test-001", actor_tg_id=creator.tg_id, backup_reference="test-backup"
        )
        assert replay["replayed"] is True
        assert (await session.execute(select(NatSeasonResetOperation))).scalars().one().status == "COMPLETED"
    await engine.dispose()
    print("NATBIRZHA controlled season reset: PASS")


if __name__ == "__main__":
    asyncio.run(run_async())
