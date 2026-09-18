from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.natbirzha.config import nat_settings, get_game_now, normalize_dt
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.inventory import NatInventory
from backend.natbirzha.services.recipes import RECIPES

class ProductionTickEngine:
    """
    Single unified production engine used across:
      - Manual API (POST /api/natbirzha/production/factory/produce)
      - Scheduler (background periodic ticks)
      - Offline catch-up (when player logs in after hours/days)
    Zero code duplication, 100% consistent state.
    """

    @staticmethod
    def get_effective_efficiency(company: NatCompany, factory: NatFactory) -> float:
        """
        Enforces strict specialization efficiency rules:
          - Own specialization: 1.0 (100%)
          - Licensed foreign: max 0.12 (12%)
          - Unlicensed foreign: 0.10 (10%)
        NEVER exceeds 0.12 outside own specialization!
        """
        if factory.specialization == company.specialization:
            return nat_settings.OWN_SPEC_EFFICIENCY
        if company.licensed_foreign_spec and factory.specialization == company.licensed_foreign_spec:
            return min(nat_settings.FOREIGN_LICENSED_MAX, 0.12)
        return nat_settings.FOREIGN_SPEC_EFFICIENCY

    @classmethod
    async def execute_factory_tick(
        cls,
        session: AsyncSession,
        company: NatCompany,
        factory: NatFactory,
        num_ticks: int = 1,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not factory.is_active or num_ticks <= 0:
            return {"success": False, "reason": "factory_inactive_or_zero_ticks"}

        now = now or get_game_now()
        
        # Find matching recipe for building_type
        recipe = next((r for r in RECIPES.values() if r["factory_type"] == factory.building_type), None)
        if not recipe:
            return {"success": False, "reason": f"no_recipe_for_{factory.building_type}"}

        eff = cls.get_effective_efficiency(company, factory)
        factory.efficiency = eff

        # Calculate required inputs and outputs
        level_mult = factory.level
        raw_inputs = {item: qty * level_mult * num_ticks for item, qty in recipe["inputs"].items()}
        
        # Municipal grid energy discount (10.0 MWh per tick free municipal power)
        municipal_free_energy = nat_settings.BASE_MUNICIPAL_ENERGY_TICK * num_ticks
        net_inputs = {}
        for item, qty in raw_inputs.items():
            if item in ("energy", "grid_quota"):
                net_needed = max(0.0, qty - municipal_free_energy)
                if net_needed > 0:
                    net_inputs[item] = net_needed
            else:
                net_inputs[item] = qty

        # Outputs scaled by efficiency
        outputs = {
            item: round(qty * level_mult * num_ticks * eff, 2)
            for item, qty in recipe["outputs"].items()
        }

        # Check inventory for required inputs
        for item_id, needed_qty in net_inputs.items():
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one_or_none()
            avail = inv.available_quantity if inv else 0.0
            if avail < needed_qty:
                return {
                    "success": False,
                    "reason": f"insufficient_{item_id}",
                    "needed": needed_qty,
                    "available": avail
                }

        # Deduct net inputs
        for item_id, needed_qty in net_inputs.items():
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one_or_none()
            inv.quantity -= needed_qty

        # Credit outputs
        for item_id, produced_qty in outputs.items():
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one_or_none()
            if not inv:
                inv = NatInventory(
                    company_id=company.id,
                    item_id=item_id,
                    quantity=produced_qty,
                    reserved_quantity=0.0,
                    avg_cost_basis=0.0
                )
                session.add(inv)
            else:
                inv.quantity += produced_qty

        # Award experience
        xp_gain = max(1, int(sum(outputs.values()) * 5))
        company.xp += xp_gain
        # Level up threshold: Level L requires 150 * L XP
        while company.level < 10 and company.xp >= company.level * 150:
            company.level += 1

        factory.last_produced_at = now
        await session.flush()

        return {
            "success": True,
            "efficiency": eff,
            "inputs_consumed": net_inputs,
            "outputs_produced": outputs,
            "xp_gained": xp_gain,
            "company_level": company.level
        }

    @classmethod
    async def execute_manual_produce(
        cls,
        session: AsyncSession,
        company_id: int,
        factory_id: int
    ) -> Dict[str, Any]:
        """Manual trigger from API: executes 1 production cycle via unified engine."""
        comp_res = await session.execute(select(NatCompany).where(NatCompany.id == company_id))
        company = comp_res.scalar_one_or_none()
        if not company:
            return {"success": False, "reason": "company_not_found"}

        fac_res = await session.execute(
            select(NatFactory).where(
                NatFactory.id == factory_id,
                NatFactory.company_id == company_id
            )
        )
        factory = fac_res.scalar_one_or_none()
        if not factory:
            return {"success": False, "reason": "factory_not_found"}

        return await cls.execute_factory_tick(session, company, factory, num_ticks=1)

    @classmethod
    async def catch_up_company(
        cls,
        session: AsyncSession,
        company_id: int,
        now: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Offline catch-up: calculates elapsed time up to max 72h and executes as many ticks as resources allow."""
        now = normalize_dt(now or get_game_now())
        comp_res = await session.execute(select(NatCompany).where(NatCompany.id == company_id))
        company = comp_res.scalar_one_or_none()
        if not company or company.is_bankrupt:
            return []

        fac_res = await session.execute(
            select(NatFactory).where(NatFactory.company_id == company_id, NatFactory.is_active == True)
        )
        factories = fac_res.scalars().all()

        results = []
        for fac in factories:
            fac_last = normalize_dt(fac.last_produced_at) if fac.last_produced_at else now
            elapsed_seconds = max(0, (now - fac_last).total_seconds())
            # Cap at 72 hours (4320 minutes)
            elapsed_minutes = min(4320, int(elapsed_seconds // 60))
            if elapsed_minutes <= 0:
                continue

            recipe = next((r for r in RECIPES.values() if r["factory_type"] == fac.building_type), None)
            if not recipe:
                continue

            # Determine maximum ticks executable with current inventory
            max_possible_ticks = elapsed_minutes
            level_mult = fac.level
            for item_id, per_tick_qty in recipe["inputs"].items():
                if item_id in ("energy", "grid_quota"):
                    net_per_tick = max(0.0, per_tick_qty * level_mult - nat_settings.BASE_MUNICIPAL_ENERGY_TICK)
                else:
                    net_per_tick = per_tick_qty * level_mult

                if net_per_tick > 0:
                    inv_res = await session.execute(
                        select(NatInventory).where(
                            NatInventory.company_id == company.id,
                            NatInventory.item_id == item_id
                        )
                    )
                    inv = inv_res.scalar_one_or_none()
                    avail = inv.available_quantity if inv else 0.0
                    ticks_for_item = int(avail // net_per_tick)
                    max_possible_ticks = min(max_possible_ticks, ticks_for_item)

            if max_possible_ticks > 0:
                res = await cls.execute_factory_tick(session, company, fac, num_ticks=max_possible_ticks, now=now)
                results.append({"factory_id": fac.id, "ticks": max_possible_ticks, "result": res})
            else:
                fac.last_produced_at = now

        if factories:
            await session.commit()

        return results

    @classmethod
    async def process_global_scheduled_tick(cls, session: AsyncSession) -> Dict[str, Any]:
        """Periodic background scheduler trigger: ticks all active factories."""
        fac_res = await session.execute(
            select(NatFactory, NatCompany)
            .join(NatCompany, NatFactory.company_id == NatCompany.id)
            .where(NatFactory.is_active == True, NatCompany.is_bankrupt == False)
        )
        rows = fac_res.all()
        ticked_count = 0
        now = get_game_now()
        for factory, company in rows:
            res = await cls.execute_factory_tick(session, company, factory, num_ticks=1, now=now)
            if res.get("success"):
                ticked_count += 1
        await session.commit()
        return {"success": True, "ticks_processed": ticked_count}
