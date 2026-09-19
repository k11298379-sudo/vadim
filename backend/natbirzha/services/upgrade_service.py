from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.services.building_catalog import get_building_spec


class UpgradeService:
    """Server-authoritative upgrade pricing, requirements and effects."""

    MAX_LEVELS = {"workers": 5, "automation": 5, "technology": 5, "level": 5}

    @staticmethod
    def workers_level(factory: NatFactory) -> int:
        spec = get_building_spec(factory.building_type) or {}
        base = int(spec.get("workers_required", 10))
        return max(0, (int(factory.workers) - base) // 10)

    @classmethod
    def current_level(cls, factory: NatFactory, kind: str) -> int:
        return {
            "workers": cls.workers_level(factory),
            "automation": int(factory.automation_level),
            "technology": int(factory.technology_level),
            "level": int(factory.level),
        }[kind]

    @classmethod
    def cost(cls, factory: NatFactory, kind: str) -> float:
        current = cls.current_level(factory, kind)
        if kind == "workers":
            return round(1800.0 * (current + 1) * max(1, factory.level), 2)
        if kind == "automation":
            return round(3500.0 * (current + 1) * max(1, factory.level), 2)
        if kind == "technology":
            return round(5000.0 * (current + 1) * max(1, factory.level), 2)
        if kind == "level":
            return round(8000.0 * (current + 1), 2)
        raise ValueError("Unknown upgrade type")

    @classmethod
    def effect_text(cls, factory: NatFactory, kind: str) -> str:
        if kind == "workers":
            return "+5% выпуска за уровень работников"
        if kind == "automation":
            return "-10% времени цикла за уровень (до -50%)"
        if kind == "technology":
            return "+8% выпуска за технологический уровень"
        if kind == "level":
            return "+1 базовый множитель выпуска и расхода сырья"
        raise ValueError("Unknown upgrade type")

    @classmethod
    def describe(cls, company: NatCompany, factory: NatFactory, kind: str) -> Dict[str, Any]:
        if kind not in cls.MAX_LEVELS:
            raise ValueError("Unknown upgrade type")
        current = cls.current_level(factory, kind)
        maximum = cls.MAX_LEVELS[kind]
        next_level = current + 1
        allowed = current < maximum
        reason = None
        if kind == "level" and next_level > company.level:
            allowed = False
            reason = f"Требуется уровень компании {next_level}"
        elif kind in ("automation", "technology") and next_level > company.level:
            allowed = False
            reason = f"Требуется уровень компании {next_level}"
        elif current >= maximum:
            reason = "Достигнут максимальный уровень"
        cost = cls.cost(factory, kind)
        if allowed and company.cash < cost:
            allowed = False
            reason = f"Недостаточно cash: нужно {cost:.0f}"
        labels = {
            "workers": "Работники",
            "automation": "Автоматизация",
            "technology": "Технологии",
            "level": "Уровень завода",
        }
        current_display = factory.workers if kind == "workers" else current
        next_display = factory.workers + 10 if kind == "workers" and current < maximum else min(next_level, maximum)
        return {
            "type": kind,
            "label": labels[kind],
            "current": current_display,
            "next": next_display,
            "current_level": current,
            "next_level": min(next_level, maximum),
            "max_level": maximum,
            "cost": cost,
            "effect": cls.effect_text(factory, kind),
            "allowed": allowed,
            "reason": reason,
        }

    @classmethod
    async def upgrade(
        cls, session: AsyncSession, company: NatCompany, factory_id: int, kind: str
    ) -> Dict[str, Any]:
        kind = kind.strip().lower()
        if kind not in cls.MAX_LEVELS:
            raise ValueError(f"Unknown upgrade type: '{kind}'")

        locked_company = (await session.execute(
            select(NatCompany).where(NatCompany.id == company.id).with_for_update()
        )).scalar_one_or_none()
        if not locked_company:
            raise ValueError("Company not found")
        company = locked_company

        result = await session.execute(
            select(NatFactory).where(
                NatFactory.id == factory_id,
                NatFactory.company_id == company.id,
            ).with_for_update()
        )
        factory = result.scalar_one_or_none()
        if not factory:
            raise ValueError("Factory not found")

        info = cls.describe(company, factory, kind)
        if not info["allowed"]:
            raise ValueError(info["reason"] or "Upgrade unavailable")

        company.cash = round(company.cash - info["cost"], 2)
        if kind == "workers":
            factory.workers += 10
        elif kind == "automation":
            factory.automation_level += 1
        elif kind == "technology":
            factory.technology_level += 1
        else:
            factory.level += 1

        await session.flush()
        return {
            "success": True,
            "factory_id": factory.id,
            "upgrade_type": kind,
            "cost_paid": info["cost"],
            "remaining_cash": company.cash,
            "level": factory.level,
            "workers": factory.workers,
            "workers_level": cls.workers_level(factory),
            "automation_level": factory.automation_level,
            "technology_level": factory.technology_level,
        }


__all__ = ["UpgradeService"]
