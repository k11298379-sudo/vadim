from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from backend.natbirzha.config import get_game_now, nat_settings
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.market import NatMarketOrder
from backend.natbirzha.models.military import NatTournament
from backend.natbirzha.models.creator import (
    NatStateTreasury,
    NatCreatorAuditLog,
    NatMarketRestriction,
    NatMarketWarning,
    NatStateBond
)
from backend.natbirzha.services.military_service import MilitaryService

class CreatorService:
    @staticmethod
    async def get_or_create_treasury(session: AsyncSession) -> NatStateTreasury:
        res = await session.execute(select(NatStateTreasury).limit(1))
        treasury = res.scalar_one_or_none()
        if not treasury:
            treasury = NatStateTreasury(cash=10000000.0, updated_at=get_game_now())
            session.add(treasury)
            await session.commit()
            await session.refresh(treasury)
        return treasury

    @classmethod
    async def get_overview(cls, session: AsyncSession) -> Dict[str, Any]:
        treasury = await cls.get_or_create_treasury(session)
        comp_count = (await session.execute(select(func.count(NatCompany.id)))).scalar() or 0
        factory_count = (await session.execute(select(func.count(NatFactory.id)))).scalar() or 0
        active_orders = (await session.execute(
            select(func.count(NatMarketOrder.id)).where(NatMarketOrder.status == "ACTIVE")
        )).scalar() or 0
        active_restr = (await session.execute(
            select(func.count(NatMarketRestriction.id)).where(NatMarketRestriction.is_active == True)
        )).scalar() or 0
        active_bonds = (await session.execute(
            select(func.count(NatStateBond.id)).where(NatStateBond.is_active == True)
        )).scalar() or 0
        total_cash_circ = (await session.execute(select(func.sum(NatCompany.cash)))).scalar() or 0.0

        return {
            "treasury_cash": treasury.cash,
            "total_companies": comp_count,
            "total_factories": factory_count,
            "active_orders": active_orders,
            "active_restrictions": active_restr,
            "active_bonds": active_bonds,
            "cash_in_circulation": round(float(total_cash_circ), 2),
            "game_time": get_game_now().isoformat()
        }

    @staticmethod
    async def get_market_snapshot(session: AsyncSession) -> Dict[str, Any]:
        orders_res = await session.execute(
            select(NatMarketOrder)
            .where(NatMarketOrder.status == "ACTIVE")
            .order_by(NatMarketOrder.created_at.desc())
            .limit(50)
        )
        orders = [
            {
                "id": o.id, "company_id": o.company_id, "order_type": o.order_type,
                "item_id": o.item_id, "price": o.price, "remaining_qty": o.remaining_qty,
                "created_at": o.created_at.isoformat()
            }
            for o in orders_res.scalars().all()
        ]

        now = get_game_now()
        restr_res = await session.execute(
            select(NatMarketRestriction)
            .where(
                NatMarketRestriction.is_active == True,
                or_(NatMarketRestriction.expires_at == None, NatMarketRestriction.expires_at > now)
            )
            .order_by(NatMarketRestriction.created_at.desc())
        )
        restrictions = [
            {
                "id": r.id, "company_id": r.company_id, "item_id": r.item_id,
                "min_price": r.min_price, "max_price": r.max_price,
                "reason": r.reason, "created_at": r.created_at.isoformat()
            }
            for r in restr_res.scalars().all()
        ]

        warn_res = await session.execute(
            select(NatMarketWarning).order_by(NatMarketWarning.created_at.desc()).limit(20)
        )
        warnings = [
            {"id": w.id, "company_id": w.company_id, "reason": w.reason, "created_at": w.created_at.isoformat()}
            for w in warn_res.scalars().all()
        ]

        return {"orders": orders, "restrictions": restrictions, "warnings": warnings}

    @staticmethod
    async def add_warning(session: AsyncSession, actor_id: int, company_id: int, reason: str) -> Dict[str, Any]:
        comp = await session.get(NatCompany, company_id)
        if not comp:
            raise ValueError("Company not found.")
        now = get_game_now()
        warning = NatMarketWarning(company_id=company_id, reason=reason, actor_id=actor_id, created_at=now)
        session.add(warning)

        log = NatCreatorAuditLog(
            actor_id=actor_id, action="WARNING_ISSUED", target_type="company",
            target_id=str(company_id), details=f"Причина: {reason}", created_at=now
        )
        session.add(log)
        await session.commit()
        return {"success": True, "warning_id": warning.id, "company_id": company_id}

    @staticmethod
    async def set_restriction(
        session: AsyncSession,
        actor_id: int,
        company_id: Optional[int],
        item_id: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        reason: str,
        duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        now = get_game_now()
        expires_at = (now + timedelta(minutes=duration_minutes)) if duration_minutes else None

        restr = NatMarketRestriction(
            company_id=company_id,
            item_id=item_id,
            min_price=min_price,
            max_price=max_price,
            reason=reason,
            actor_id=actor_id,
            is_active=True,
            expires_at=expires_at,
            created_at=now
        )
        session.add(restr)

        log = NatCreatorAuditLog(
            actor_id=actor_id, action="RESTRICTION_SET", target_type="market",
            target_id=f"item:{item_id}|comp:{company_id}",
            details=f"Диапазон: [{min_price}, {max_price}] ₽. Причина: {reason}",
            created_at=now
        )
        session.add(log)
        await session.commit()
        await session.refresh(restr)
        return {
            "success": True, "restriction_id": restr.id, "min_price": min_price,
            "max_price": max_price, "expires_at": expires_at.isoformat() if expires_at else None
        }

    @staticmethod
    async def remove_restriction(session: AsyncSession, actor_id: int, restriction_id: int) -> Dict[str, Any]:
        restr = await session.get(NatMarketRestriction, restriction_id)
        if not restr or not restr.is_active:
            raise ValueError("Active restriction not found.")
        restr.is_active = False

        log = NatCreatorAuditLog(
            actor_id=actor_id, action="RESTRICTION_REMOVED", target_type="restriction",
            target_id=str(restriction_id), details=f"Снято ограничение {restr.reason}", created_at=get_game_now()
        )
        session.add(log)
        await session.commit()
        return {"success": True, "removed_id": restriction_id}

    @staticmethod
    async def check_market_restriction(
        session: AsyncSession, company_id: int, item_id: str, price: float
    ) -> Tuple[bool, Optional[str]]:
        now = get_game_now()
        restr_res = await session.execute(
            select(NatMarketRestriction).where(
                NatMarketRestriction.is_active == True,
                or_(NatMarketRestriction.expires_at == None, NatMarketRestriction.expires_at > now),
                or_(NatMarketRestriction.company_id == None, NatMarketRestriction.company_id == company_id),
                or_(NatMarketRestriction.item_id == None, NatMarketRestriction.item_id == item_id)
            )
        )
        for r in restr_res.scalars().all():
            if r.min_price is not None and price < r.min_price:
                return False, f"Цена {price} ₽ ниже установленного государством минимума {r.min_price} ₽ ({r.reason})"
            if r.max_price is not None and price > r.max_price:
                return False, f"Цена {price} ₽ выше установленного государством максимума {r.max_price} ₽ ({r.reason})"
        return True, None

    @classmethod
    async def issue_bonds(
        cls, session: AsyncSession, actor_id: int, title: str, volume: int,
        face_value: float, coupon_rate: float, maturity_days: int, purpose: str
    ) -> Dict[str, Any]:
        if volume <= 0 or face_value <= 0 or maturity_days <= 0:
            raise ValueError("Volume, face value, and maturity must be positive.")

        treasury = await cls.get_or_create_treasury(session)
        now = get_game_now()
        bond = NatStateBond(
            title=title, total_volume=volume, remaining_volume=volume,
            face_value=face_value, coupon_rate=coupon_rate, maturity_days=maturity_days,
            purpose=purpose, actor_id=actor_id, is_active=True, created_at=now
        )
        session.add(bond)

        # Treasury receives funds from the bond placement
        raised_funds = round(volume * face_value, 2)
        treasury.cash += raised_funds
        treasury.updated_at = now

        log = NatCreatorAuditLog(
            actor_id=actor_id, action="BOND_ISSUANCE", target_type="bond",
            target_id=title, details=f"Выпуск {volume} шт. на сумму {raised_funds} ₽. Цель: {purpose}",
            created_at=now
        )
        session.add(log)
        await session.commit()
        await session.refresh(bond)
        return {
            "success": True, "bond_id": bond.id, "title": bond.title,
            "raised_funds": raised_funds, "treasury_cash": treasury.cash
        }

    @staticmethod
    async def get_bonds(session: AsyncSession) -> List[Dict[str, Any]]:
        res = await session.execute(select(NatStateBond).order_by(NatStateBond.created_at.desc()))
        return [
            {
                "id": b.id, "title": b.title, "total_volume": b.total_volume,
                "remaining_volume": b.remaining_volume, "face_value": b.face_value,
                "coupon_rate": b.coupon_rate, "maturity_days": b.maturity_days,
                "purpose": b.purpose, "is_active": b.is_active, "created_at": b.created_at.isoformat()
            }
            for b in res.scalars().all()
        ]

    @staticmethod
    async def launch_early_tournament(session: AsyncSession, actor_id: int) -> Dict[str, Any]:
        now = get_game_now()
        curr_res = await session.execute(
            select(NatTournament).where(NatTournament.status == "PENDING").order_by(NatTournament.id.desc()).limit(1)
        )
        curr = curr_res.scalar_one_or_none()
        if curr:
            res = await MilitaryService.resolve_tournament(session, curr.id)
            log_detail = f"Досрочно завершён турнир #{curr.tournament_number}"
        else:
            latest_num_res = await session.execute(select(func.max(NatTournament.tournament_number)))
            next_num = (latest_num_res.scalar() or 0) + 1
            new_tourn = NatTournament(
                tournament_number=next_num,
                start_time=now,
                snapshot_time=now + timedelta(hours=72),
                finish_time=now + timedelta(hours=72),
                status="PENDING",
                prize_pool_nat=100
            )
            session.add(new_tourn)
            await session.commit()
            res = {"status": "created", "tournament_id": new_tourn.id, "tournament_number": next_num}
            log_detail = f"Запущен новый турнир #{next_num}"

        log = NatCreatorAuditLog(
            actor_id=actor_id, action="EARLY_TOURNAMENT_LAUNCH", target_type="tournament",
            target_id=str(res.get("tournament_id", "")), details=log_detail, created_at=now
        )
        session.add(log)
        await session.commit()
        return {"success": True, "result": res}

    @staticmethod
    async def get_audit_log(session: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
        res = await session.execute(
            select(NatCreatorAuditLog).order_by(NatCreatorAuditLog.created_at.desc()).limit(limit)
        )
        return [
            {
                "id": l.id, "actor_id": l.actor_id, "action": l.action,
                "target_type": l.target_type, "target_id": l.target_id,
                "details": l.details, "created_at": l.created_at.isoformat()
            }
            for l in res.scalars().all()
        ]
