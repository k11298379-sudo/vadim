from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.natbirzha.config import get_game_now, normalize_dt, nat_settings
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.inventory import NatInventory
from backend.natbirzha.services.recipes import RECIPES

class ProductionTickEngine:
    """Single deterministic engine for starting, completing and catching up cycles."""

    @staticmethod
    def recipe_for(factory: NatFactory, recipe_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if recipe_id and recipe_id in RECIPES:
            recipe = RECIPES[recipe_id]
            return recipe if recipe["factory_type"] == factory.building_type else None
        return next((r for r in RECIPES.values() if r["factory_type"] == factory.building_type), None)

    @staticmethod
    def get_effective_efficiency(company: NatCompany, factory: NatFactory) -> float:
        if factory.specialization == company.specialization:
            return min(1.0, nat_settings.OWN_SPEC_EFFICIENCY)
        if company.licensed_foreign_spec == factory.specialization:
            return min(0.12, nat_settings.FOREIGN_LICENSED_MAX)
        return min(0.10, nat_settings.FOREIGN_SPEC_EFFICIENCY)

    @staticmethod
    def cycle_duration_seconds(factory: NatFactory, recipe: Dict[str, Any]) -> int:
        base = max(10, int(recipe.get("base_duration", 60)))
        # Automation makes cycles faster, but never removes the interaction loop.
        reduction = min(0.60, factory.automation_level * 0.10)
        return max(10, int(round(base * (1.0 - reduction))))

    @staticmethod
    def upgrade_cost(factory: NatFactory, kind: str) -> float:
        level = factory.level
        if kind == "workers":
            return round(1200 * (level + factory.workers // 10), 2)
        if kind == "automation":
            return round(3000 * (factory.automation_level + 1), 2)
        if kind == "technology":
            return round(4500 * (factory.technology_level + 1), 2)
        if kind == "level":
            return round(7000 * (level + 1), 2)
        raise ValueError("Unknown upgrade type")

    @staticmethod
    async def _inventory(session: AsyncSession, company_id: int, item_id: str) -> Optional[NatInventory]:
        res = await session.execute(select(NatInventory).where(
            NatInventory.company_id == company_id, NatInventory.item_id == item_id
        ))
        return res.scalar_one_or_none()

    @classmethod
    async def start_cycle(cls, session: AsyncSession, company: NatCompany, factory: NatFactory,
                          recipe_id: Optional[str] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
        if not factory.is_active:
            return {"success": False, "reason": "factory_inactive"}
        if factory.cycle_ready_at:
            ready = normalize_dt(factory.cycle_ready_at)
            current = normalize_dt(now or get_game_now())
            if current >= ready:
                return {"success": False, "reason": "cycle_ready_to_collect"}
            return {"success": False, "reason": "cycle_in_progress", "ready_at": ready.isoformat()}

        recipe = cls.recipe_for(factory, recipe_id)
        if not recipe:
            return {"success": False, "reason": "recipe_not_available"}
        if company.level < recipe.get("level_req", 1):
            return {"success": False, "reason": "company_level_required", "required_level": recipe["level_req"]}

        eff = cls.get_effective_efficiency(company, factory)
        multiplier = max(1, factory.level)
        for item_id, qty in recipe["inputs"].items():
            needed = round(qty * multiplier, 2)
            inv = await cls._inventory(session, company.id, item_id)
            available = inv.available_quantity if inv else 0.0
            if available < needed:
                # Auto-grant starter operational reserve if company lacks starter inputs
                from backend.natbirzha.services.company_service import STARTER_INVENTORIES
                bundle = STARTER_INVENTORIES.get(company.specialization, {})
                if item_id in bundle and (inv is None or inv.quantity <= 0.0):
                    grant_qty = bundle[item_id]
                    if not inv:
                        inv = NatInventory(
                            company_id=company.id, item_id=item_id,
                            quantity=grant_qty, reserved_quantity=0.0, avg_cost_basis=0.0
                        )
                        session.add(inv)
                    else:
                        inv.quantity = grant_qty
                    await session.flush()
                    available = inv.available_quantity

            if available < needed:
                return {"success": False, "reason": f"insufficient_{item_id}", "needed": needed, "available": available}


        # Inputs are consumed at cycle start, so resources cannot be double-spent while processing.
        for item_id, qty in recipe["inputs"].items():
            inv = await cls._inventory(session, company.id, item_id)
            inv.quantity = round(inv.quantity - qty * multiplier, 2)

        current = normalize_dt(now or get_game_now())
        duration = cls.cycle_duration_seconds(factory, recipe)
        factory.current_recipe = next(k for k, v in RECIPES.items() if v is recipe)
        factory.cycle_started_at = current
        factory.cycle_ready_at = current + timedelta(seconds=duration)
        factory.cycle_input_cost = 0.0
        await session.flush()
        from backend.natbirzha.config import get_game_tz
        tz = get_game_tz()
        c_iso = (current.replace(tzinfo=tz) if current.tzinfo is None else current).isoformat()
        r_iso = (factory.cycle_ready_at.replace(tzinfo=tz) if factory.cycle_ready_at.tzinfo is None else factory.cycle_ready_at).isoformat()
        return {"success": True, "status": "running", "recipe_id": factory.current_recipe,
                "started_at": c_iso, "ready_at": r_iso,
                "duration_seconds": duration, "efficiency": eff}

    @classmethod
    async def complete_cycle(cls, session: AsyncSession, company: NatCompany, factory: NatFactory,
                             now: Optional[datetime] = None) -> Dict[str, Any]:
        if not factory.cycle_ready_at or not factory.current_recipe:
            return {"success": False, "reason": "no_cycle_in_progress"}
        current = normalize_dt(now or get_game_now())
        ready = normalize_dt(factory.cycle_ready_at)
        if current < ready:
            remaining = max(0, int((ready - current).total_seconds()))
            from backend.natbirzha.config import get_game_tz
            r_iso = (ready.replace(tzinfo=get_game_tz()) if ready.tzinfo is None else ready).isoformat()
            return {"success": False, "reason": "cycle_in_progress", "remaining_seconds": remaining,
                    "ready_at": r_iso}

        recipe = RECIPES.get(factory.current_recipe)
        if not recipe:
            return {"success": False, "reason": "recipe_missing"}
        eff = cls.get_effective_efficiency(company, factory)
        multiplier = max(1, factory.level)
        outputs = {item: round(qty * multiplier * eff, 2) for item, qty in recipe["outputs"].items()}
        for item_id, qty in outputs.items():
            inv = await cls._inventory(session, company.id, item_id)
            if not inv:
                inv = NatInventory(company_id=company.id, item_id=item_id, quantity=0.0,
                                   reserved_quantity=0.0, avg_cost_basis=0.0)
                session.add(inv)
            inv.quantity = round(inv.quantity + qty, 2)

        xp_gain = max(1, int(sum(outputs.values()) * 5))
        company.xp += xp_gain
        while company.level < 10 and company.xp >= company.level * 150:
            company.level += 1
        factory.last_produced_at = current
        recipe_id = factory.current_recipe
        factory.current_recipe = None
        factory.cycle_started_at = None
        factory.cycle_ready_at = None
        factory.cycle_input_cost = 0.0
        await session.flush()
        return {"success": True, "status": "completed", "recipe_id": recipe_id,
                "outputs_produced": outputs, "xp_gained": xp_gain, "company_level": company.level}

    @classmethod
    async def execute_manual_produce(cls, session: AsyncSession, company_id: int, factory_id: int,
                                     recipe_id: Optional[str] = None) -> Dict[str, Any]:
        company = await session.get(NatCompany, company_id)
        factory = await session.get(NatFactory, factory_id)
        if not company or not factory or factory.company_id != company_id:
            return {"success": False, "reason": "factory_not_found"}
        now = normalize_dt(get_game_now())
        if factory.cycle_ready_at:
            ready = normalize_dt(factory.cycle_ready_at)
            if now >= ready:
                return await cls.complete_cycle(session, company, factory, now)
            remaining = max(1, int((ready - now).total_seconds()))
            return {
                "success": False,
                "reason": "cycle_in_progress",
                "remaining_seconds": remaining,
                "ready_at": ready.isoformat()
            }
        return await cls.start_cycle(session, company, factory, recipe_id, now)


    @classmethod
    async def catch_up_company(cls, session: AsyncSession, company_id: int,
                               now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        company = await session.get(NatCompany, company_id)
        if not company or company.is_bankrupt:
            return []
        current = normalize_dt(now or get_game_now())
        res = await session.execute(select(NatFactory).where(NatFactory.company_id == company_id,
                                                              NatFactory.is_active == True))
        factories = res.scalars().all()
        results = []
        for factory in factories:
            if factory.cycle_ready_at and current >= normalize_dt(factory.cycle_ready_at):
                results.append(await cls.complete_cycle(session, company, factory, current))
            fac_last = normalize_dt(factory.last_produced_at) if factory.last_produced_at else current
            elapsed_minutes = min(4320, int(max(0, (current - fac_last).total_seconds()) // 60))
            if elapsed_minutes > 0:
                recipe = cls.recipe_for(factory, factory.current_recipe)
                if recipe:
                    max_ticks = elapsed_minutes
                    mult = factory.level
                    for item_id, per_tick in recipe["inputs"].items():
                        net = max(0.0, per_tick * mult - (nat_settings.BASE_MUNICIPAL_ENERGY_TICK if item_id in ("energy", "grid_quota") else 0.0))
                        if net > 0:
                            inv = await cls._inventory(session, company.id, item_id)
                            avail = inv.available_quantity if inv else 0.0
                            max_ticks = min(max_ticks, int(avail // net))
                    if max_ticks > 0:
                        eff = cls.get_effective_efficiency(company, factory)
                        for item_id, per_tick in recipe["inputs"].items():
                            net = max(0.0, per_tick * mult * max_ticks - (nat_settings.BASE_MUNICIPAL_ENERGY_TICK * max_ticks if item_id in ("energy", "grid_quota") else 0.0))
                            if net > 0:
                                inv = await cls._inventory(session, company.id, item_id)
                                if inv:
                                    inv.quantity = round(inv.quantity - net, 2)
                        outputs = {item: round(qty * mult * max_ticks * eff, 2) for item, qty in recipe["outputs"].items()}
                        for item_id, qty in outputs.items():
                            inv = await cls._inventory(session, company.id, item_id)
                            if not inv:
                                inv = NatInventory(company_id=company.id, item_id=item_id, quantity=0.0, reserved_quantity=0.0, avg_cost_basis=0.0)
                                session.add(inv)
                            inv.quantity = round(inv.quantity + qty, 2)
                        xp_gain = max(1, int(sum(outputs.values()) * 5))
                        company.xp += xp_gain
                        while company.level < 10 and company.xp >= company.level * 150:
                            company.level += 1
                        results.append({"factory_id": factory.id, "ticks": max_ticks, "outputs": outputs})
                factory.last_produced_at = current
        await session.commit()
        return results

    @classmethod
    async def process_global_scheduled_tick(cls, session: AsyncSession) -> Dict[str, Any]:
        now = normalize_dt(get_game_now())
        res = await session.execute(select(NatFactory, NatCompany).join(NatCompany, NatFactory.company_id == NatCompany.id)
                                    .where(NatFactory.is_active == True, NatCompany.is_bankrupt == False))
        completed = 0
        for factory, company in res.all():
            if factory.cycle_ready_at and now >= normalize_dt(factory.cycle_ready_at):
                result = await cls.complete_cycle(session, company, factory, now)
                completed += int(result.get("success", False))
        await session.commit()
        return {"success": True, "ticks_processed": completed, "cycles_completed": completed}
