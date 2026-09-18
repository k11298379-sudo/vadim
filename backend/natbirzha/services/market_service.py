from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.natbirzha.config import get_game_now, get_game_today
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.inventory import NatInventory, CANONICAL_ITEMS
from backend.natbirzha.models.market import NatMarketOrder, NatMarketTrade
from backend.natbirzha.models.restructuring import NatDailyFinancials

class MarketService:
    @staticmethod
    async def get_orderbook(session: AsyncSession, item_id: str) -> Dict[str, Any]:
        if item_id not in CANONICAL_ITEMS:
            raise ValueError(f"Unknown item: {item_id}")

        bids_res = await session.execute(
            select(NatMarketOrder)
            .where(
                NatMarketOrder.item_id == item_id,
                NatMarketOrder.order_type == "BUY",
                NatMarketOrder.status == "ACTIVE",
                NatMarketOrder.remaining_qty > 0
            )
            .order_by(NatMarketOrder.price.desc(), NatMarketOrder.created_at.asc())
            .limit(20)
        )
        bids = [
            {"id": o.id, "price": o.price, "remaining_qty": o.remaining_qty, "company_id": o.company_id}
            for o in bids_res.scalars().all()
        ]

        asks_res = await session.execute(
            select(NatMarketOrder)
            .where(
                NatMarketOrder.item_id == item_id,
                NatMarketOrder.order_type == "SELL",
                NatMarketOrder.status == "ACTIVE",
                NatMarketOrder.remaining_qty > 0
            )
            .order_by(NatMarketOrder.price.asc(), NatMarketOrder.created_at.asc())
            .limit(20)
        )
        asks = [
            {"id": o.id, "price": o.price, "remaining_qty": o.remaining_qty, "company_id": o.company_id}
            for o in asks_res.scalars().all()
        ]

        return {"item_id": item_id, "bids": bids, "asks": asks}

    @classmethod
    async def create_order(
        cls,
        session: AsyncSession,
        company: NatCompany,
        order_type: str,
        item_id: str,
        price: float,
        quantity: float
    ) -> NatMarketOrder:
        order_type = order_type.upper()
        if order_type not in ("BUY", "SELL"):
            raise ValueError("Invalid order type: must be BUY or SELL.")
        if item_id not in CANONICAL_ITEMS:
            raise ValueError(f"Unknown item: {item_id}")
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive.")

        now = get_game_now()

        if order_type == "BUY":
            total_cost = round(price * quantity, 2)
            if company.cash < total_cost:
                raise ValueError(f"Insufficient cash. Required: {total_cost}, Available: {company.cash}")
            company.cash -= total_cost
        elif order_type == "SELL":
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == item_id
                )
            )
            inv = inv_res.scalar_one_or_none()
            if not inv or inv.available_quantity < quantity:
                avail = inv.available_quantity if inv else 0.0
                raise ValueError(f"Insufficient inventory to sell. Required: {quantity}, Available: {avail}")
            inv.reserved_quantity += quantity

        order = NatMarketOrder(
            company_id=company.id,
            order_type=order_type,
            item_id=item_id,
            price=price,
            quantity=quantity,
            remaining_qty=quantity,
            status="ACTIVE",
            created_at=now
        )
        session.add(order)
        await session.flush()

        # Trigger immediate matching against opposite book
        await cls.match_orders_for_item(session, item_id)
        await session.commit()
        await session.refresh(order)
        return order

    @classmethod
    async def match_orders_for_item(cls, session: AsyncSession, item_id: str) -> int:
        trades_count = 0
        now = get_game_now()

        while True:
            # Get best buy order (highest price, earliest timestamp)
            buy_res = await session.execute(
                select(NatMarketOrder)
                .where(
                    NatMarketOrder.item_id == item_id,
                    NatMarketOrder.order_type == "BUY",
                    NatMarketOrder.status == "ACTIVE",
                    NatMarketOrder.remaining_qty > 0
                )
                .order_by(NatMarketOrder.price.desc(), NatMarketOrder.created_at.asc())
                .limit(1)
            )
            buy_order = buy_res.scalar_one_or_none()

            # Get best sell order (lowest price, earliest timestamp)
            sell_res = await session.execute(
                select(NatMarketOrder)
                .where(
                    NatMarketOrder.item_id == item_id,
                    NatMarketOrder.order_type == "SELL",
                    NatMarketOrder.status == "ACTIVE",
                    NatMarketOrder.remaining_qty > 0
                )
                .order_by(NatMarketOrder.price.asc(), NatMarketOrder.created_at.asc())
                .limit(1)
            )
            sell_order = sell_res.scalar_one_or_none()

            if not buy_order or not sell_order:
                break
            if buy_order.price < sell_order.price:
                # Spread is not crossed
                break
            if buy_order.company_id == sell_order.company_id:
                # Wash trade prevention: skip or cancel self-matching
                break

            # Determine execution price (maker price: earlier order's price)
            trade_price = sell_order.price if sell_order.created_at <= buy_order.created_at else buy_order.price
            trade_qty = min(buy_order.remaining_qty, sell_order.remaining_qty)
            total_amount = round(trade_price * trade_qty, 2)
            fee = round(total_amount * 0.01, 2)  # 1% exchange fee

            # Load Buyer and Seller
            buyer_comp = await session.get(NatCompany, buy_order.company_id)
            seller_comp = await session.get(NatCompany, sell_order.company_id)

            # Buyer already paid buy_order.price * quantity. If executed lower, refund diff
            price_diff = round((buy_order.price - trade_price) * trade_qty, 2)
            if price_diff > 0:
                buyer_comp.cash += price_diff

            # Seller receives trade_price - fee
            seller_comp.cash += round(total_amount - fee, 2)

            # Transfer inventory from seller to buyer
            seller_inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == seller_comp.id,
                    NatInventory.item_id == item_id
                )
            )
            seller_inv = seller_inv_res.scalar_one()
            seller_inv.quantity -= trade_qty
            seller_inv.reserved_quantity -= trade_qty

            buyer_inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == buyer_comp.id,
                    NatInventory.item_id == item_id
                )
            )
            buyer_inv = buyer_inv_res.scalar_one_or_none()
            if not buyer_inv:
                buyer_inv = NatInventory(
                    company_id=buyer_comp.id,
                    item_id=item_id,
                    quantity=trade_qty,
                    reserved_quantity=0.0,
                    avg_cost_basis=trade_price
                )
                session.add(buyer_inv)
            else:
                buyer_inv.quantity += trade_qty

            # Update orders
            buy_order.remaining_qty -= trade_qty
            if buy_order.remaining_qty <= 0:
                buy_order.status = "FILLED"
                buy_order.closed_at = now

            sell_order.remaining_qty -= trade_qty
            if sell_order.remaining_qty <= 0:
                sell_order.status = "FILLED"
                sell_order.closed_at = now

            trade = NatMarketTrade(
                buy_order_id=buy_order.id,
                sell_order_id=sell_order.id,
                buyer_company_id=buyer_comp.id,
                seller_company_id=seller_comp.id,
                item_id=item_id,
                price=trade_price,
                quantity=trade_qty,
                total_amount=total_amount,
                fee_amount=fee,
                executed_at=now
            )
            session.add(trade)

            # Update daily financials for buyer (opex) and seller (revenue)
            today = get_game_today()
            for comp_id, rev_delta, opex_delta in [
                (buyer_comp.id, 0.0, total_amount),
                (seller_comp.id, round(total_amount - fee, 2), 0.0)
            ]:
                f_res = await session.execute(
                    select(NatDailyFinancials).where(
                        NatDailyFinancials.company_id == comp_id,
                        NatDailyFinancials.calendar_date == today
                    )
                )
                fin = f_res.scalar_one_or_none()
                if not fin:
                    fin = NatDailyFinancials(
                        company_id=comp_id,
                        calendar_date=today,
                        gross_revenue=rev_delta,
                        opex=opex_delta,
                        closed_profit=round(rev_delta - opex_delta, 2),
                        developer_fee_paid=0.0
                    )
                    session.add(fin)
                else:
                    fin.gross_revenue += rev_delta
                    fin.opex += opex_delta
                    fin.closed_profit = round(fin.gross_revenue - fin.opex, 2)

            trades_count += 1
            await session.flush()

        return trades_count

    @classmethod
    async def cancel_order(cls, session: AsyncSession, company: NatCompany, order_id: int) -> bool:
        order_res = await session.execute(
            select(NatMarketOrder).where(
                NatMarketOrder.id == order_id,
                NatMarketOrder.company_id == company.id,
                NatMarketOrder.status == "ACTIVE"
            )
        )
        order = order_res.scalar_one_or_none()
        if not order:
            return False

        if order.order_type == "BUY":
            refund_amount = round(order.price * order.remaining_qty, 2)
            company.cash += refund_amount
        elif order.order_type == "SELL":
            inv_res = await session.execute(
                select(NatInventory).where(
                    NatInventory.company_id == company.id,
                    NatInventory.item_id == order.item_id
                )
            )
            inv = inv_res.scalar_one()
            inv.reserved_quantity = max(0.0, inv.reserved_quantity - order.remaining_qty)

        order.status = "CANCELLED"
        order.closed_at = get_game_now()
        await session.commit()
        return True
