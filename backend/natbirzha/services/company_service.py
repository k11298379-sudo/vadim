from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.natbirzha.config import nat_settings, get_game_now, get_game_today, normalize_dt
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.inventory import NatInventory, get_item_base_price
from backend.natbirzha.models.military import NatArmy
from backend.natbirzha.services.recipes import RECIPES

VALID_SPECIALIZATIONS = {
    "agrarian": "Аграрий",
    "miner": "Горнодобытчик",
    "metallurgist": "Металлург",
    "oilman": "Нефтяник",
    "power_engineer": "Энергетик",
    "forester": "Лесопромышленник",
    "chemist": "Химик",
    "technoprom": "Технопром",
}

SPECIALIZATION_ALIASES = {
    "metallurgy": "metallurgist",
    "metallurgist": "metallurgist",
    "energy": "power_engineer",
    "power_engineer": "power_engineer",
    "oil_gas": "oilman",
    "oilman": "oilman",
    "agriculture": "agrarian",
    "agrarian": "agrarian",
    "chemicals": "chemist",
    "chemist": "chemist",
    "forester": "forester",
    "forestry": "forester",
    "miner": "miner",
    "mining": "miner",
    "technoprom": "technoprom",
    "electronics": "technoprom",
    "construction": "miner",
    "it_telecom": "technoprom",
}

STARTER_FACTORIES = {
    "agrarian": "farm_grain",
    "miner": "iron_mine",
    "metallurgist": "steel_mill",
    "oilman": "oil_rig",
    "power_engineer": "solar_plant",
    "forester": "logging_camp",
    "chemist": "chemical_plant",
    "technoprom": "component_factory",
}

STARTER_INVENTORIES: Dict[str, Dict[str, float]] = {
    "agrarian": {"water": 100.0, "grid_quota": 100.0},
    "miner": {"water": 100.0, "grid_quota": 100.0},
    "oilman": {"water": 100.0, "grid_quota": 100.0},
    "forester": {"water": 100.0, "grid_quota": 100.0},
    "power_engineer": {"water": 100.0, "grid_quota": 100.0},
    "metallurgist": {"water": 100.0, "grid_quota": 100.0, "iron_ore": 60.0, "coal": 40.0, "energy": 60.0},
    "chemist": {"water": 100.0, "grid_quota": 100.0, "oil_crude": 40.0, "energy": 60.0},
    "technoprom": {"water": 100.0, "grid_quota": 100.0, "copper": 40.0, "plastics": 40.0, "energy": 60.0},
}

class CompanyService:
    @staticmethod
    async def create_company(
        session: AsyncSession,
        user_id: int,
        name: str,
        specialization: str
    ) -> NatCompany:
        spec = SPECIALIZATION_ALIASES.get(specialization.lower(), specialization)
        if spec not in VALID_SPECIALIZATIONS:
            raise ValueError(f"Invalid specialization: {specialization}")

        clean_name = name.strip()
        if len(clean_name) < 2 or len(clean_name) > 64:
            raise ValueError("Company name must be between 2 and 64 characters.")

        existing = await session.execute(select(NatCompany).where(NatCompany.user_id == user_id))
        if existing.scalar_one_or_none():
            raise ValueError("User already owns a company.")

        now = get_game_now()
        company = NatCompany(
            user_id=user_id,
            name=clean_name,
            specialization=spec,
            level=1,
            xp=0,
            cash=nat_settings.STARTING_CASH,
            nat_balance=0,
            territory_tiles=nat_settings.STARTING_TERRITORY_TILES,
            max_territory=20,
            is_bankrupt=False,
            created_at=now,
            updated_at=now
        )
        session.add(company)
        await session.flush()

        # Build initial starter factory
        if spec not in STARTER_FACTORIES:
            raise ValueError(f"Unknown specialization: {specialization}")
        b_type = STARTER_FACTORIES[spec]
        default_recipe = next((k for k, v in RECIPES.items() if v.get("factory_type") == b_type), None)
        starter_factory = NatFactory(
            company_id=company.id,
            building_type=b_type,
            specialization=spec,
            level=1,
            efficiency=1.0,
            is_active=True,
            workers=10,
            automation_level=0,
            current_recipe=default_recipe,
            last_produced_at=now,
            created_at=now
        )
        session.add(starter_factory)

        # Starter utilities and raw resources keep every specialization playable from minute one.
        starter_items = STARTER_INVENTORIES.get(spec, {"water": 100.0, "grid_quota": 100.0})
        for item_id, quantity in starter_items.items():
            session.add(NatInventory(
                company_id=company.id, item_id=item_id, quantity=quantity,
                reserved_quantity=0.0, avg_cost_basis=0.0
            ))


        # Initialize base army garrison
        army = NatArmy(
            company_id=company.id,
            infantry=10,
            tanks=0,
            drones=0,
            air_defense=0,
            army_strength=100,
            updated_at=now
        )
        session.add(army)

        await session.commit()
        await session.refresh(company)
        return company

    @staticmethod
    async def get_by_owner_id(session: AsyncSession, user_id: int) -> Optional[NatCompany]:
        """Find company by internal User.id or Telegram tg_id."""
        res = await session.execute(select(NatCompany).where(NatCompany.user_id == user_id))
        comp = res.scalar_one_or_none()
        if comp:
            return comp
        from backend.db.models import User
        user_res = await session.execute(select(User).where(User.tg_id == user_id))
        user = user_res.scalar_one_or_none()
        if user:
            res = await session.execute(select(NatCompany).where(NatCompany.user_id == user.id))
            return res.scalar_one_or_none()
        return None

    @staticmethod
    async def calculate_nav(session: AsyncSession, company: NatCompany) -> float:
        """Alias for calculate_audited_nav."""
        return await CompanyService.calculate_audited_nav(session, company)

    @staticmethod
    async def calculate_audited_nav(session: AsyncSession, company: NatCompany) -> float:
        """Calculates Net Asset Value: Cash + Land + Factories + Inventory."""
        total_nav = float(company.cash)
        # Land valuation: 10,000 cash per tile
        total_nav += company.territory_tiles * 10000.0

        # Factories valuation: 25,000 cash per level
        fac_res = await session.execute(select(NatFactory).where(NatFactory.company_id == company.id))
        factories = fac_res.scalars().all()
        for f in factories:
            total_nav += f.level * 25000.0

        # Inventory valuation at base price
        inv_res = await session.execute(select(NatInventory).where(NatInventory.company_id == company.id))
        inventory = inv_res.scalars().all()
        for it in inventory:
            if it.quantity > 0:
                try:
                    total_nav += it.quantity * get_item_base_price(it.item_id)
                except ValueError:
                    pass

        return round(total_nav, 2)

    @staticmethod
    async def change_specialization(
        session: AsyncSession,
        company: NatCompany,
        new_specialization: str
    ) -> Dict[str, Any]:
        """Respec specialization with 7-day cooldown and 25% NAV fee."""
        if new_specialization not in VALID_SPECIALIZATIONS:
            raise ValueError("Invalid specialization.")
        if new_specialization == company.specialization:
            raise ValueError("Company already has this specialization.")

        now = normalize_dt(get_game_now())
        if company.last_respec_at:
            last_respec = normalize_dt(company.last_respec_at)
            elapsed = (now - last_respec).total_seconds() / 86400
            if elapsed < nat_settings.RESPEC_COOLDOWN_DAYS:
                remaining = round(nat_settings.RESPEC_COOLDOWN_DAYS - elapsed, 1)
                raise ValueError(f"Respec cooldown active. Wait {remaining} days.")

        nav = await CompanyService.calculate_audited_nav(session, company)
        fee = round(nav * nat_settings.RESPEC_COST_PCT, 2)
        if company.cash < fee:
            raise ValueError(f"Insufficient cash for respec fee. Needed: {fee}, Available: {company.cash}")

        company.cash -= fee
        company.specialization = new_specialization
        company.last_respec_at = now

        # Immediately update all existing factories: old factories drop to 10%
        fac_res = await session.execute(select(NatFactory).where(NatFactory.company_id == company.id))
        for f in fac_res.scalars().all():
            if f.specialization == new_specialization:
                f.efficiency = 1.0
            else:
                f.efficiency = nat_settings.FOREIGN_SPEC_EFFICIENCY

        await session.commit()
        return {"success": True, "new_specialization": new_specialization, "fee_paid": fee}

    @staticmethod
    async def buy_foreign_license(
        session: AsyncSession,
        company: NatCompany,
        target_spec: str
    ) -> Dict[str, Any]:
        """NAT currency sink: Purchase secondary industry foreign license (up to 12% eff)."""
        if target_spec not in VALID_SPECIALIZATIONS:
            raise ValueError("Invalid target specialization.")
        if target_spec == company.specialization:
            raise ValueError("Cannot license own primary specialization.")
        if company.licensed_foreign_spec == target_spec:
            raise ValueError(f"Company already holds license for {target_spec}.")

        cost = nat_settings.FOREIGN_LICENSE_COST_NAT
        if company.nat_balance < cost:
            raise ValueError(f"Insufficient NAT balance. Required: {cost} NAT, Available: {company.nat_balance} NAT.")

        company.nat_balance -= cost
        company.licensed_foreign_spec = target_spec

        # Boost matching foreign factories to licensed cap (12%)
        fac_res = await session.execute(select(NatFactory).where(NatFactory.company_id == company.id))
        for f in fac_res.scalars().all():
            if f.specialization == target_spec:
                f.efficiency = nat_settings.FOREIGN_LICENSED_MAX

        await session.commit()
        return {
            "success": True,
            "licensed_foreign_spec": target_spec,
            "cost_paid_nat": cost,
            "remaining_nat_balance": company.nat_balance
        }

