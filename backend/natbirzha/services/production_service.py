import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.natbirzha.config import get_game_now, normalize_dt, nat_settings
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.inventory import NatInventory
from backend.natbirzha.services.recipes import get_recipe, get_recipe_for_factory
from backend.natbirzha.services.upgrade_service import UpgradeService
from backend.natbirzha.services.premium_service import PremiumLicenseRequired, PremiumService


class ProductionTickEngine:
    """Authoritative timed production state machine: IDLE -> RUNNING -> READY -> IDLE."""

    _factory_locks: Dict[int, asyncio.Lock] = {}

    @classmethod
    def _get_lock(cls, factory_id: int) -> asyncio.Lock:
        cls._factory_locks.setdefault(factory_id, asyncio.Lock())
        return cls._factory_locks[factory_id]

    @staticmethod
    def recipe_for(factory: NatFactory, recipe_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        recipe = get_recipe(recipe_id) if recipe_id else get_recipe_for_factory(factory.building_type)
        if not recipe:
            return None
        if recipe["factory_type"] != factory.building_type:
            return None
        if recipe["specialization"] != factory.specialization:
            return None
        return recipe

    @staticmethod
    def get_effective_efficiency(company: NatCompany, factory: NatFactory) -> float:
        if factory.specialization == company.specialization:
            return min(1.0, nat_settings.OWN_SPEC_EFFICIENCY)
        if company.licensed_foreign_spec == factory.specialization:
            return min(0.12, nat_settings.FOREIGN_LICENSED_MAX)
        return min(0.10, nat_settings.FOREIGN_SPEC_EFFICIENCY)

    @staticmethod
    def cycle_duration_seconds(factory: NatFactory, recipe: Dict[str, Any]) -> int:
        base = max(15, int(recipe.get("duration") or recipe.get("base_duration", 60)))
        level_add = max(0, (factory.level - 1) * 15)
        reduction = min(0.50, factory.automation_level * 0.10)
        return max(15, int(round((base + level_add) * (1.0 - reduction))))

    @staticmethod
    def output_multiplier(factory: NatFactory) -> float:
        workers_bonus = 1.0 + UpgradeService.workers_level(factory) * 0.05
        technology_bonus = 1.0 + factory.technology_level * 0.08
        return max(1, factory.level) * workers_bonus * technology_bonus

    @staticmethod
    def upgrade_cost(factory: NatFactory, kind: str) -> float:
        return UpgradeService.cost(factory, kind)

    @staticmethod
    async def _inventory(
        session: AsyncSession,
        company_id: int,
        item_id: str,
        for_update: bool = False,
    ) -> Optional[NatInventory]:
        stmt = select(NatInventory).where(
            NatInventory.company_id == company_id,
            NatInventory.item_id == item_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def start_cycle(
        cls,
        session: AsyncSession,
        company: NatCompany,
        factory: NatFactory,
        recipe_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        async with cls._get_lock(factory.id):
            locked_company = (await session.execute(
                select(NatCompany).where(NatCompany.id == company.id).with_for_update()
            )).scalar_one_or_none()
            if not locked_company:
                return {"success": False, "reason": "company_not_found"}
            company = locked_company
            locked = (await session.execute(
                select(NatFactory).where(
                    NatFactory.id == factory.id,
                    NatFactory.company_id == company.id,
                ).with_for_update()
            )).scalar_one_or_none()
            if not locked:
                return {"success": False, "reason": "factory_not_found"}
            return await cls._start_cycle_locked(session, company, locked, recipe_id, now)

    @classmethod
    async def _start_cycle_locked(
        cls,
        session: AsyncSession,
        company: NatCompany,
        factory: NatFactory,
        recipe_id: Optional[str],
        now: Optional[datetime],
    ) -> Dict[str, Any]:
        if not factory.is_active:
            return {"success": False, "reason": "factory_inactive"}

        current = normalize_dt(now or get_game_now())
        if factory.cycle_ready_at or factory.cycle_started_at:
            ready = normalize_dt(factory.cycle_ready_at)
            if ready and current >= ready:
                return {"success": False, "reason": "cycle_ready_to_collect"}
            return {
                "success": False,
                "reason": "cycle_in_progress",
                "ready_at": ready.isoformat() if ready else None,
            }

        recipe = cls.recipe_for(factory, recipe_id)
        if not recipe:
            return {"success": False, "reason": "recipe_not_available"}
        if company.level < recipe.get("level_req", 1):
            return {
                "success": False,
                "reason": "company_level_required",
                "required_level": recipe["level_req"],
            }

        required_license = recipe.get("required_license")
        if required_license:
            try:
                await PremiumService.require_active_license(
                    session, company.id, required_license, now=current
                )
            except PremiumLicenseRequired:
                return {
                    "success": False,
                    "reason": "premium_license_required",
                    "required_license": required_license,
                }

        labor_demand = int(recipe.get("labor_demand", 0))
        if labor_demand > 0 and factory.workers < labor_demand:
            return {
                "success": False,
                "reason": "insufficient_labor",
                "needed": labor_demand,
                "available": factory.workers,
            }

        input_multiplier = max(1, factory.level)
        requirements: Dict[str, float] = {}
        locked_inputs: Dict[str, NatInventory] = {}
        for item_id, quantity in recipe["inputs"].items():
            needed = round(float(quantity) * input_multiplier, 4)
            requirements[item_id] = needed
            inv = await cls._inventory(session, company.id, item_id, for_update=True)
            available = inv.available_quantity if inv else 0.0
            if available < needed:
                return {
                    "success": False,
                    "reason": f"insufficient_{item_id}",
                    "needed": needed,
                    "available": available,
                }
            locked_inputs[item_id] = inv

        for item_id, needed in requirements.items():
            inv = locked_inputs[item_id]
            inv.quantity = round(inv.quantity - needed, 4)

        duration = cls.cycle_duration_seconds(factory, recipe)
        factory.current_recipe = str(recipe["recipe_id"])
        factory.cycle_started_at = current
        factory.cycle_ready_at = current + timedelta(seconds=duration)
        factory.cycle_input_cost = 0.0
        await session.flush()

        from backend.natbirzha.config import get_game_tz
        tz = get_game_tz()
        started = current.replace(tzinfo=tz) if current.tzinfo is None else current
        ready = factory.cycle_ready_at.replace(tzinfo=tz) if factory.cycle_ready_at.tzinfo is None else factory.cycle_ready_at
        return {
            "success": True,
            "status": "running",
            "recipe_id": factory.current_recipe,
            "started_at": started.isoformat(),
            "ready_at": ready.isoformat(),
            "duration_seconds": duration,
            "remaining_seconds": duration,
            "efficiency": cls.get_effective_efficiency(company, factory),
        }

    @classmethod
    async def complete_cycle(
        cls,
        session: AsyncSession,
        company: NatCompany,
        factory: NatFactory,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        async with cls._get_lock(factory.id):
            locked_company = (await session.execute(
                select(NatCompany).where(NatCompany.id == company.id).with_for_update()
            )).scalar_one_or_none()
            if not locked_company:
                return {"success": False, "reason": "company_not_found"}
            company = locked_company
            locked = (await session.execute(
                select(NatFactory).where(
                    NatFactory.id == factory.id,
                    NatFactory.company_id == company.id,
                ).with_for_update()
            )).scalar_one_or_none()
            if not locked:
                return {"success": False, "reason": "factory_not_found"}
            return await cls._complete_cycle_locked(session, company, locked, now)

    @classmethod
    async def _complete_cycle_locked(
        cls,
        session: AsyncSession,
        company: NatCompany,
        factory: NatFactory,
        now: Optional[datetime],
    ) -> Dict[str, Any]:
        if not factory.cycle_ready_at or not factory.current_recipe:
            return {"success": False, "reason": "no_cycle_in_progress"}

        current = normalize_dt(now or get_game_now())
        ready = normalize_dt(factory.cycle_ready_at)
        if current < ready:
            return {
                "success": False,
                "reason": "cycle_in_progress",
                "remaining_seconds": max(1, int((ready - current).total_seconds())),
            }

        recipe = get_recipe(factory.current_recipe)
        if not recipe or recipe["factory_type"] != factory.building_type:
            return {"success": False, "reason": "recipe_missing"}

        efficiency = cls.get_effective_efficiency(company, factory)
        multiplier = cls.output_multiplier(factory) * efficiency
        outputs = {
            item_id: round(float(quantity) * multiplier, 4)
            for item_id, quantity in recipe["outputs"].items()
        }

        cap = float(nat_settings.INVENTORY_MAX_QUANTITY_PER_ITEM)
        output_inventory: Dict[str, NatInventory] = {}
        for item_id, quantity in outputs.items():
            inv = await cls._inventory(session, company.id, item_id, for_update=True)
            existing = inv.quantity if inv else 0.0
            if existing + quantity > cap:
                return {
                    "success": False,
                    "reason": "inventory_overflow",
                    "item_id": item_id,
                    "capacity": cap,
                    "current": existing,
                    "incoming": quantity,
                }
            if not inv:
                inv = NatInventory(
                    company_id=company.id,
                    item_id=item_id,
                    quantity=0.0,
                    reserved_quantity=0.0,
                    avg_cost_basis=0.0,
                )
                session.add(inv)
            output_inventory[item_id] = inv

        for item_id, quantity in outputs.items():
            output_inventory[item_id].quantity = round(output_inventory[item_id].quantity + quantity, 4)

        xp_gain = max(1, int(sum(outputs.values()) * 5))
        company.xp += xp_gain
        while company.level < 10 and company.xp >= company.level * 150:
            company.level += 1

        recipe_id = factory.current_recipe
        factory.last_produced_at = current
        factory.current_recipe = None
        factory.cycle_started_at = None
        factory.cycle_ready_at = None
        factory.cycle_input_cost = 0.0
        await session.flush()
        return {
            "success": True,
            "status": "completed",
            "recipe_id": recipe_id,
            "outputs_produced": outputs,
            "xp_gained": xp_gain,
            "company_level": company.level,
        }

    @classmethod
    async def execute_manual_produce(
        cls,
        session: AsyncSession,
        company_id: int,
        factory_id: int,
        recipe_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        company = await session.get(NatCompany, company_id)
        factory = await session.get(NatFactory, factory_id)
        if not company or not factory or factory.company_id != company_id:
            return {"success": False, "reason": "factory_not_found"}
        now = normalize_dt(get_game_now())
        if factory.cycle_ready_at:
            if now >= normalize_dt(factory.cycle_ready_at):
                return await cls.complete_cycle(session, company, factory, now)
            return {
                "success": False,
                "reason": "cycle_in_progress",
                "remaining_seconds": max(1, int((normalize_dt(factory.cycle_ready_at) - now).total_seconds())),
            }
        return await cls.start_cycle(session, company, factory, recipe_id, now)

    @classmethod
    async def catch_up_company(
        cls,
        session: AsyncSession,
        company_id: int,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Complete only cycles explicitly started before the player went offline."""
        company = await session.get(NatCompany, company_id)
        if not company or company.is_bankrupt:
            return []
        current = normalize_dt(now or get_game_now())
        result = await session.execute(
            select(NatFactory).where(
                NatFactory.company_id == company_id,
                NatFactory.is_active == True,
            )
        )
        completed: List[Dict[str, Any]] = []
        for factory in result.scalars().all():
            if factory.cycle_ready_at and current >= normalize_dt(factory.cycle_ready_at):
                completed.append(await cls.complete_cycle(session, company, factory, current))
        await session.commit()
        return completed

    @classmethod
    async def process_global_scheduled_tick(cls, session: AsyncSession) -> Dict[str, Any]:
        now = normalize_dt(get_game_now())
        result = await session.execute(
            select(NatFactory, NatCompany)
            .join(NatCompany, NatFactory.company_id == NatCompany.id)
            .where(NatFactory.is_active == True, NatCompany.is_bankrupt == False)
        )
        completed = 0
        for factory, company in result.all():
            if factory.cycle_ready_at and now >= normalize_dt(factory.cycle_ready_at):
                cycle_result = await cls.complete_cycle(session, company, factory, now)
                completed += int(cycle_result.get("success", False))
        await session.commit()
        return {"success": True, "ticks_processed": completed, "cycles_completed": completed}


__all__ = ["ProductionTickEngine"]
