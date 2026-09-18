from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.natbirzha.config import nat_settings, get_game_today
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.inventory import (
    NatInventory,
    CANONICAL_ITEMS,
    get_item_base_price,
    get_npc_buy_price,
    get_npc_sell_price
)
from backend.natbirzha.models.restructuring import NatDailyFinancials

class NPCReserveService:
    """
    State Reserve (Госрезерв) providing floor and ceiling liquidity.
    Enables single-player and low-population economies to operate without deadlocks.
    """

    @staticmethod
    def get_npc_quote(item_id: str) -> Dict[str, Any]:
        if item_id not in CANONICAL_ITEMS:
            raise ValueError(f"Unknown item: {item_id}")
        base = get_item_base_price(item_id)
        buy_floor = get_npc_buy_price(item_id)
        sell_cap = get_npc_sell_price(item_id)
        return {
            "item_id": item_id,
            "name": CANONICAL_ITEMS[item_id]["name"],
            "unit": CANONICAL_ITEMS[item_id]["unit"],
            "base_price": base,
            "npc_buy_price": buy_floor,    # Player sells to NPC at discount
            "npc_sell_price": sell_cap,   # Player buys from NPC at premium
            "spread_pct": round(((sell_cap - buy_floor) / base) * 100, 1)
        }

    @classmethod
    async def get_active_player_scaling_factor(cls, session: AsyncSession) -> float:
        res = await session.execute(select(func.count(NatCompany.id)))
        count = res.scalar() or 1
        if count <= 1:
            return nat_settings.NPC_VOLUME_SCALING_FACTORS[1]
        elif count <= 5:
            return nat_settings.NPC_VOLUME_SCALING_FACTORS[5]
        elif count <= 20:
            return nat_settings.NPC_VOLUME_SCALING_FACTORS[20]
        else:
            return nat_settings.NPC_VOLUME_SCALING_FACTORS[30]

    @classmethod
    async def execute_npc_trade(
        cls,
        session: AsyncSession,
        company: NatCompany,
        item_id: str,
        action: str,  # "BUY" (player buys from NPC) or "SELL" (player sells to NPC)
        quantity: float
    ) -> Dict[str, Any]:
        if quantity <= 0:
            return {"success": False, "reason": "invalid_quantity"}

        quote = cls.get_npc_quote(item_id)
        today = get_game_today()

        # Find or create daily financials record
        fin_res = await session.execute(
            select(NatDailyFinancials).where(
                NatDailyFinancials.company_id == company.id,
                NatDailyFinancials.calendar_date == today
            )
        )
        fin = fin_res.scalar_one_or_none()
        if not fin:
            fin = NatDailyFinancials(
                company_id=company.id,
                calendar_date=today,
                gross_revenue=0.0,
                opex=0.0,
                closed_profit=0.0
            )
            session.add(fin)

        if action == "BUY":
            # Player buys resource from NPC
            unit_price = quote["npc_sell_price"]
            total_cost = round(unit_price * quantity, 2)
            if company.cash < total_cost:
                return {
                    "success": False,
                    "reason": "insufficient_cash",
                    "needed": total_cost,
                    "available": company.cash
                }

            company.cash -= total_cost
            fin.opex += total_cost
            fin.closed_profit = round(fin.gross_revenue - fin.opex, 2)

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
                    quantity=quantity,
                    reserved_quantity=0.0,
                    avg_cost_basis=unit_price
                )
                session.add(inv)
            else:
                total_qty = inv.quantity + quantity
                if total_qty > 0:
                    inv.avg_cost_basis = round(((inv.quantity * inv.avg_cost_basis) + total_cost) / total_qty, 2)
                inv.quantity = total_qty

            await session.flush()
            return {
                "success": True,
                "action": "BUY",
                "item_id": item_id,
                "unit_price": unit_price,
                "quantity": quantity,
                "total_cost": total_cost,
                "remaining_cash": company.cash
            }

        elif action == "SELL":
            # Player sells resource to NPC
            unit_price = quote["npc_buy_price"]
            total_payout = round(unit_price * quantity, 2)

            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one_or_none()
            if not inv or inv.available_quantity < quantity:
                avail = inv.available_quantity if inv else 0.0
                return {
                    "success": False,
                    "reason": "insufficient_inventory",
                    "needed": quantity,
                    "available": avail
                }

            inv.quantity -= quantity
            company.cash += total_payout
            fin.gross_revenue += total_payout
            fin.closed_profit = round(fin.gross_revenue - fin.opex, 2)

            # XP gain for successful trade
            xp_gain = max(1, int(quantity * 2))
            company.xp += xp_gain

            await session.flush()
            return {
                "success": True,
                "action": "SELL",
                "item_id": item_id,
                "unit_price": unit_price,
                "quantity": quantity,
                "total_payout": total_payout,
                "new_cash_balance": company.cash,
                "xp_gained": xp_gain
            }
        else:
            return {"success": False, "reason": "invalid_action"}
