from typing import Dict, Any, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.natbirzha.config import get_game_now
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.services.building_catalog import (
    CANONICAL_BUILDINGS, resolve_building_type, get_building_spec, list_catalog_for_company
)
from backend.natbirzha.services.production_service import ProductionTickEngine

class BuildingService:
    @staticmethod
    def get_catalog_for_company(company: Optional[NatCompany]) -> List[Dict[str, Any]]:
        return list_catalog_for_company(company)

    @staticmethod
    async def get_building_details(session: AsyncSession, company: NatCompany, factory_id: int) -> Optional[Dict[str, Any]]:
        res = await session.execute(
            select(NatFactory).where(NatFactory.id == factory_id, NatFactory.company_id == company.id)
        )
        fac = res.scalar_one_or_none()
        if not fac:
            return None
        spec = get_building_spec(fac.building_type) or {}
        return {
            'id': fac.id,
            'building_type': fac.building_type,
            'name': spec.get('name', fac.building_type),
            'description': spec.get('description', ''),
            'specialization': fac.specialization,
            'category': spec.get('category', 'processing'),
            'level_required': spec.get('level_required', 1),
            'build_cost': spec.get('build_cost', 0.0),
            'workers_required': spec.get('workers_required', fac.workers),
            'energy_required': spec.get('energy_required', 0),
            'cycle_duration': spec.get('cycle_duration', 60),
            'inputs': spec.get('inputs', {}),
            'outputs': spec.get('outputs', {}),
            'efficiency': fac.efficiency,
            'upgrade_level': fac.level,
            'automation_level': fac.automation_level,
            'technology_level': fac.technology_level,
            'workers': fac.workers,
            'status': 'active' if fac.is_active else 'inactive',
            'cycle_ready_at': fac.cycle_ready_at.isoformat() if fac.cycle_ready_at else None
        }

    @staticmethod
    async def build_factory(
        session: AsyncSession,
        company: NatCompany,
        raw_type: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        b_type = resolve_building_type(raw_type)
        spec = get_building_spec(b_type)
        if not spec:
            raise ValueError(f"Unknown building type: '{raw_type}'")

        # 1. Level check
        if company.level < spec['level_required']:
            raise ValueError(
                f"Company level {company.level} too low. Required level: {spec['level_required']}"
            )

        # 2. Free slots check
        fac_res = await session.execute(
            select(func.count(NatFactory.id)).where(NatFactory.company_id == company.id)
        )
        existing_count = fac_res.scalar() or 0
        max_slots = max(3, 3 + (company.level - 1))
        territory_limit = company.territory_tiles or 3
        effective_max = min(max_slots, territory_limit)
        if existing_count >= effective_max:
            raise ValueError(
                f"No free construction slots. Used {existing_count}/{effective_max} slots. Expand territory or level."
            )

        # 3. Cash check and atomic deduction
        cost = float(spec['build_cost'])
        if company.cash < cost:
            raise ValueError(
                f"Insufficient cash. Cost: {cost:,.0f} cash, available: {company.cash:,.0f} cash"
            )

        # 4. Specialization efficiency (100% own, 10% foreign, max 12% licensed)
        is_own = (spec['specialization'] == company.specialization)
        is_licensed = (company.licensed_foreign_spec == spec['specialization'])
        eff = 1.0 if is_own else (0.12 if is_licensed else 0.10)

        company.cash = round(company.cash - cost, 2)
        now = get_game_now()

        factory = NatFactory(
            company_id=company.id,
            building_type=spec['id'],
            specialization=spec['specialization'],
            level=1,
            efficiency=eff,
            is_active=True,
            workers=spec['workers_required'],
            automation_level=0,
            technology_level=0,
            current_recipe=spec['recipe_id'],
            last_produced_at=now,
            created_at=now
        )
        session.add(factory)
        await session.commit()
        await session.refresh(factory)

        return {
            'success': True,
            'factory_id': factory.id,
            'building_type': factory.building_type,
            'name': spec['name'],
            'cost_paid': cost,
            'remaining_cash': company.cash,
            'efficiency': eff,
            'specialization': factory.specialization
        }

    @staticmethod
    async def upgrade_factory(
        session: AsyncSession,
        company: NatCompany,
        factory_id: int,
        upgrade_type: str
    ) -> Dict[str, Any]:
        res = await session.execute(
            select(NatFactory).where(NatFactory.id == factory_id, NatFactory.company_id == company.id)
        )
        fac = res.scalar_one_or_none()
        if not fac:
            raise ValueError('Factory not found')

        kind = upgrade_type.lower().strip()
        limits = {'workers': 100, 'automation': 5, 'technology': 5, 'level': 5}
        if kind not in limits:
            raise ValueError(f"Unknown upgrade type: '{upgrade_type}'")

        current = {
            'workers': fac.workers // 10,
            'automation': fac.automation_level,
            'technology': fac.technology_level,
            'level': fac.level
        }[kind]

        if current >= limits[kind]:
            raise ValueError('Maximum upgrade level reached')

        # Level requirements check (cannot bypass level)
        if kind == 'level' and fac.level >= company.level:
            raise ValueError(f'Factory level cannot exceed company level ({company.level})')
        if kind in ('automation', 'technology') and current >= company.level:
            raise ValueError(f'Upgrade to level {current + 1} requires higher company level ({current + 1})')

        cost = ProductionTickEngine.upgrade_cost(fac, kind)
        if company.cash < cost:
            raise ValueError(f'Insufficient cash. Required: {cost:,.0f}, available: {company.cash:,.0f}')

        company.cash = round(company.cash - cost, 2)
        if kind == 'workers':
            fac.workers += 10
        elif kind == 'automation':
            fac.automation_level += 1
        elif kind == 'technology':
            fac.technology_level += 1
        elif kind == 'level':
            fac.level += 1

        await session.commit()
        await session.refresh(fac)
        return {
            'success': True,
            'factory_id': fac.id,
            'upgrade_type': kind,
            'cost_paid': cost,
            'remaining_cash': company.cash,
            'level': fac.level,
            'workers': fac.workers,
            'automation_level': fac.automation_level,
            'technology_level': fac.technology_level
        }

__all__ = ['BuildingService']
