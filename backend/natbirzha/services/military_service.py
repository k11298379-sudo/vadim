from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from backend.natbirzha.config import nat_settings, get_game_now
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.inventory import NatInventory
from backend.natbirzha.models.military import NatArmy, NatTournament, NatTournamentParticipant
from backend.natbirzha.models.alliances import NatAlliance, NatAllianceMember

UNIT_SPECS = {
    "infantry": {"cash_cost": 50.0, "strength": 10, "items": {}},
    "tanks": {"cash_cost": 1000.0, "strength": 150, "items": {"steel": 1.0}},
    "drones": {"cash_cost": 500.0, "strength": 80, "items": {"electronics": 1.0}},
    "air_defense": {"cash_cost": 1500.0, "strength": 200, "items": {"steel": 2.0, "electronics": 1.0}},
}

class MilitaryService:
    @staticmethod
    async def recruit_units(
        session: AsyncSession,
        company: NatCompany,
        unit_type: str,
        count: int
    ) -> Dict[str, Any]:
        if unit_type not in UNIT_SPECS:
            raise ValueError(f"Unknown unit type: {unit_type}")
        if count <= 0:
            raise ValueError("Count must be positive.")

        spec = UNIT_SPECS[unit_type]
        total_cash = spec["cash_cost"] * count
        if company.cash < total_cash:
            raise ValueError(f"Insufficient cash. Required: {total_cash}, Available: {company.cash}")

        # Check required item materials
        for item_id, per_unit in spec["items"].items():
            needed = per_unit * count
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one_or_none()
            if not inv or inv.available_quantity < needed:
                avail = inv.available_quantity if inv else 0.0
                raise ValueError(f"Insufficient {item_id}. Required: {needed}, Available: {avail}")

        # Deduct cash & materials
        company.cash -= total_cash
        for item_id, per_unit in spec["items"].items():
            needed = per_unit * count
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one()
            inv.quantity -= needed

        # Fetch or create Army
        army_res = await session.execute(select(NatArmy).where(NatArmy.company_id == company.id))
        army = army_res.scalar_one_or_none()
        now = get_game_now()
        if not army:
            army = NatArmy(company_id=company.id, updated_at=now)
            session.add(army)

        current_val = getattr(army, unit_type, 0)
        setattr(army, unit_type, current_val + count)

        # Recalculate strength
        army.army_strength = (
            army.infantry * 10
            + army.tanks * 150
            + army.drones * 80
            + army.air_defense * 200
        )
        army.updated_at = now

        await session.commit()
        return {
            "success": True,
            "unit_type": unit_type,
            "count_recruited": count,
            "new_army_strength": army.army_strength,
            "remaining_cash": company.cash
        }

    @staticmethod
    async def create_alliance(
        session: AsyncSession,
        company: NatCompany,
        name: str
    ) -> Dict[str, Any]:
        """Creates a new alliance with strict max 3 members and creator as LEADER."""
        if company.is_bankrupt:
            raise ValueError("Bankrupt companies cannot create an alliance.")

        clean_name = name.strip()
        if len(clean_name) < 3 or len(clean_name) > 64:
            raise ValueError("Alliance name must be between 3 and 64 characters.")

        existing_name = await session.execute(select(NatAlliance).where(NatAlliance.name == clean_name))
        if existing_name.scalar_one_or_none():
            raise ValueError("Alliance with this name already exists.")

        existing_mem = await session.execute(
            select(NatAllianceMember).where(NatAllianceMember.company_id == company.id)
        )
        if existing_mem.scalar_one_or_none():
            raise ValueError("Company is already in an alliance.")

        now = get_game_now()
        alliance = NatAlliance(
            name=clean_name,
            leader_company_id=company.id,
            member_count=1,
            max_members=nat_settings.ALLIANCE_MAX_MEMBERS,
            total_army_strength=0,
            created_at=now
        )
        session.add(alliance)
        await session.flush()

        member = NatAllianceMember(
            alliance_id=alliance.id,
            company_id=company.id,
            role="LEADER",
            joined_at=now
        )
        session.add(member)
        await session.commit()
        await session.refresh(alliance)
        return {
            "success": True,
            "alliance_id": alliance.id,
            "name": alliance.name,
            "member_count": alliance.member_count,
            "role": "LEADER"
        }

    @staticmethod
    async def leave_alliance(session: AsyncSession, company: NatCompany) -> Dict[str, Any]:
        """Leaves the current alliance. If leader leaves, transfers leadership or disbands."""
        mem_res = await session.execute(
            select(NatAllianceMember).where(NatAllianceMember.company_id == company.id)
        )
        member = mem_res.scalar_one_or_none()
        if not member:
            raise ValueError("Company is not in any alliance.")

        alliance_id = member.alliance_id
        alliance = await session.get(NatAlliance, alliance_id)
        await session.delete(member)
        await session.flush()

        if alliance:
            alliance.member_count = max(0, alliance.member_count - 1)
            next_mem_res = await session.execute(
                select(NatAllianceMember).where(NatAllianceMember.alliance_id == alliance_id)
            )
            remaining_members = next_mem_res.scalars().all()
            if not remaining_members:
                await session.delete(alliance)
            elif alliance.leader_company_id == company.id:
                new_leader = remaining_members[0]
                new_leader.role = "LEADER"
                alliance.leader_company_id = new_leader.company_id

        await session.commit()
        return {"success": True, "left_alliance_id": alliance_id}

    @staticmethod
    async def get_company_alliance(session: AsyncSession, company_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves alliance and member roster for a given company."""
        mem_res = await session.execute(
            select(NatAllianceMember).where(NatAllianceMember.company_id == company_id)
        )
        member = mem_res.scalar_one_or_none()
        if not member:
            return None

        alliance = await session.get(NatAlliance, member.alliance_id)
        if not alliance:
            return None

        members_res = await session.execute(
            select(NatAllianceMember, NatCompany)
            .join(NatCompany, NatAllianceMember.company_id == NatCompany.id)
            .where(NatAllianceMember.alliance_id == alliance.id)
        )
        members_list = [
            {
                "company_id": c.id,
                "company_name": c.name,
                "role": m.role,
                "joined_at": str(m.joined_at)
            }
            for m, c in members_res.all()
        ]
        return {
            "id": alliance.id,
            "name": alliance.name,
            "leader_company_id": alliance.leader_company_id,
            "member_count": alliance.member_count,
            "max_members": alliance.max_members,
            "my_role": member.role,
            "members": members_list
        }

    @staticmethod
    async def join_alliance(
        session: AsyncSession,
        alliance_id: int,
        company: NatCompany
    ) -> Dict[str, Any]:
        """Strictly enforces maximum 3 members. Rejects 4th candidate."""
        if company.is_bankrupt:
            raise ValueError("Bankrupt companies cannot join an alliance.")

        alliance_res = await session.execute(select(NatAlliance).where(NatAlliance.id == alliance_id))
        alliance = alliance_res.scalar_one_or_none()
        if not alliance:
            raise ValueError("Alliance not found.")

        # Atomic check on member limit
        members_count_res = await session.execute(
            select(func.count(NatAllianceMember.id)).where(NatAllianceMember.alliance_id == alliance.id)
        )
        current_members = members_count_res.scalar() or 0
        if current_members >= nat_settings.ALLIANCE_MAX_MEMBERS:
            raise ValueError(f"Alliance is full. Maximum {nat_settings.ALLIANCE_MAX_MEMBERS} members allowed.")

        # Check if already in an alliance
        existing_mem = await session.execute(
            select(NatAllianceMember).where(NatAllianceMember.company_id == company.id)
        )
        if existing_mem.scalar_one_or_none():
            raise ValueError("Company is already in an alliance.")

        member = NatAllianceMember(
            alliance_id=alliance.id,
            company_id=company.id,
            role="MEMBER",
            joined_at=get_game_now()
        )
        session.add(member)
        alliance.member_count = current_members + 1
        await session.commit()
        return {"success": True, "alliance_id": alliance.id, "member_count": alliance.member_count}

    @staticmethod
    async def resolve_tournament(session: AsyncSession, tournament_id: int) -> Dict[str, Any]:
        """
        Resolves 72h tournament ranking.
        CRITERION: ONLY ARMY STRENGTH.
        TIE POLICY: Earliest-Timestamp (ORDER BY snapshot_strength DESC, army_updated_at ASC, company_id ASC).
        1st place receives 100 NAT.
        """
        tourn = await session.get(NatTournament, tournament_id)
        if not tourn:
            raise ValueError("Tournament not found.")

        # Order strictly by strength desc, earliest timestamp asc, company_id asc
        ranking_res = await session.execute(
            select(NatTournamentParticipant)
            .where(NatTournamentParticipant.tournament_id == tournament_id)
            .order_by(
                NatTournamentParticipant.snapshot_strength.desc(),
                NatTournamentParticipant.army_updated_at.asc(),
                NatTournamentParticipant.company_id.asc()
            )
        )
        participants = ranking_res.scalars().all()
        if not participants:
            tourn.status = "COMPLETED"
            await session.commit()
            return {"status": "no_participants"}

        winner_participant = participants[0]
        winner_company = await session.get(NatCompany, winner_participant.company_id)
        
        # Award 100 NAT to 1st place
        winner_company.nat_balance += nat_settings.TOURNAMENT_WINNER_PRIZE_NAT
        winner_participant.prize_nat = nat_settings.TOURNAMENT_WINNER_PRIZE_NAT
        winner_participant.final_rank = 1

        for rank_idx, p in enumerate(participants[1:], start=2):
            p.final_rank = rank_idx
            p.prize_nat = 0

        tourn.status = "COMPLETED"
        await session.commit()

        return {
            "status": "completed",
            "tournament_id": tournament_id,
            "winner_company_id": winner_company.id,
            "winner_name": winner_company.name,
            "winner_strength": winner_participant.snapshot_strength,
            "prize_awarded_nat": nat_settings.TOURNAMENT_WINNER_PRIZE_NAT
        }
