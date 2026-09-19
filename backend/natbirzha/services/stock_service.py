from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.natbirzha.config import nat_settings, get_game_now, get_game_today
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.stocks import NatStock, NatStockHolding, NatStockOrder
from backend.natbirzha.models.restructuring import NatDailyFinancials
from backend.natbirzha.services.company_service import CompanyService

class ValuationStrategy(ABC):
    @abstractmethod
    def calculate_valuation(self, nav: float, cash: float, recent_closed_profits: List[float]) -> float:
        pass

class DefaultWeightedValuationStrategy(ValuationStrategy):
    """
    Pluggable runtime valuation formula.
    Can be modified or replaced without database migrations!
    """
    def calculate_valuation(self, nav: float, cash: float, recent_closed_profits: List[float]) -> float:
        avg_profit = sum(recent_closed_profits) / max(1, len(recent_closed_profits))
        val = (
            nav * nat_settings.IPO_NAV_WEIGHT
            + max(0.0, avg_profit) * nat_settings.IPO_PROFIT_PE_MULT
            + cash * nat_settings.IPO_CASH_DISCOUNT
        )
        return max(50000.0, round(val, 2))

current_valuation_strategy: ValuationStrategy = DefaultWeightedValuationStrategy()


class StockService:
    @staticmethod
    async def apply_for_ipo(
        session: AsyncSession,
        company: NatCompany,
        strategy: Optional[ValuationStrategy] = None
    ) -> NatStock:
        if company.level < nat_settings.IPO_MIN_LEVEL:
            raise ValueError(f"Company level must be at least {nat_settings.IPO_MIN_LEVEL} for IPO.")
        if company.is_bankrupt:
            raise ValueError("Bankrupt companies cannot apply for IPO.")

        # Check if already actively listed
        existing_stock = await session.execute(
            select(NatStock).where(NatStock.company_id == company.id, NatStock.is_listed == True)
        )
        if existing_stock.scalar_one_or_none():
            raise ValueError("Company is already public.")

        # Check at least 1-3 closed days of profit history
        fin_res = await session.execute(
            select(NatDailyFinancials)
            .where(NatDailyFinancials.company_id == company.id)
            .order_by(NatDailyFinancials.calendar_date.desc())
            .limit(3)
        )
        fin_records = fin_res.scalars().all()
        profits = [r.closed_profit for r in fin_records]
        if not profits:
            # Fallback for vertical playable slice onboarding
            profits = [company.cash * 0.1]

        strat = strategy or current_valuation_strategy
        nav = await CompanyService.calculate_audited_nav(session, company)
        valuation = strat.calculate_valuation(nav, company.cash, profits)

        total_shares = nat_settings.IPO_MIN_SHARES
        founder_shares = int(total_shares * nat_settings.IPO_FOUNDER_MIN_PCT)  # 6000
        float_shares = total_shares - founder_shares                           # 4000
        share_price = round(valuation / total_shares, 2)

        now = get_game_now()
        stock = NatStock(
            company_id=company.id,
            total_shares=total_shares,
            founder_shares=founder_shares,
            float_shares=float_shares,
            current_price=share_price,
            last_valuation=valuation,
            is_listed=True,
            ipo_date=now,
            created_at=now
        )
        session.add(stock)
        await session.flush()

        # Allocate founder holding (60%)
        founder_holding = NatStockHolding(
            stock_id=stock.id,
            holder_company_id=company.id,
            shares_count=founder_shares,
            avg_price=share_price,
            updated_at=now
        )
        session.add(founder_holding)

        # Place float shares (40%) on market
        float_order = NatStockOrder(
            stock_id=stock.id,
            trader_company_id=company.id,
            order_type="SELL",
            shares_count=float_shares,
            remaining_shares=float_shares,
            price=share_price,
            status="ACTIVE",
            created_at=now
        )
        session.add(float_order)

        await session.commit()
        await session.refresh(stock)
        return stock

    @staticmethod
    async def buy_shares(
        session: AsyncSession,
        buyer_company: NatCompany,
        stock_id: int,
        shares_to_buy: int
    ) -> Dict[str, Any]:
        """Buys available float shares from market orderbook."""
        if shares_to_buy <= 0:
            raise ValueError("Shares count must be positive.")

        if buyer_company.is_bankrupt:
            raise ValueError("Bankrupt companies cannot purchase stocks.")

        stock = await session.scalar(
            select(NatStock).where(
                NatStock.id == stock_id,
                NatStock.is_listed == True,
            ).with_for_update()
        )
        if not stock:
            raise ValueError("Stock is not actively listed.")

        order_res = await session.execute(
            select(NatStockOrder).where(
                NatStockOrder.stock_id == stock_id,
                NatStockOrder.order_type == "SELL",
                NatStockOrder.status == "ACTIVE",
                NatStockOrder.remaining_shares > 0
            )
            .order_by(NatStockOrder.price.asc(), NatStockOrder.created_at.asc())
        )
        order = order_res.scalar_one_or_none()
        if not order:
            raise ValueError("No active sell orders for this stock.")

        executed_shares = min(shares_to_buy, order.remaining_shares)
        total_cost = round(executed_shares * order.price, 2)
        if buyer_company.cash < total_cost:
            raise ValueError(f"Insufficient cash. Required: {total_cost}, Available: {buyer_company.cash}")

        buyer_company.cash -= total_cost

        # Credit proceeds to issuer or seller
        seller_comp = await session.get(NatCompany, order.trader_company_id)
        if seller_comp:
            seller_comp.cash += total_cost

        order.remaining_shares -= executed_shares
        if order.remaining_shares <= 0:
            order.status = "FILLED"
        # float_shares is the currently available free-float shown in quotes,
        # not the immutable IPO allocation. Keep it synchronized with orders.
        stock.float_shares = max(0, int(stock.float_shares) - int(executed_shares))

        # Update buyer holding
        now = get_game_now()
        hold_res = await session.execute(
            select(NatStockHolding).where(
                NatStockHolding.stock_id == stock_id,
                NatStockHolding.holder_company_id == buyer_company.id
            )
        )
        holding = hold_res.scalar_one_or_none()
        if not holding:
            holding = NatStockHolding(
                stock_id=stock_id,
                holder_company_id=buyer_company.id,
                shares_count=executed_shares,
                avg_price=order.price,
                updated_at=now
            )
            session.add(holding)
        else:
            total_s = holding.shares_count + executed_shares
            if total_s > 0:
                holding.avg_price = round(((holding.shares_count * holding.avg_price) + total_cost) / total_s, 2)
            holding.shares_count = total_s
            holding.updated_at = now

        # Update the last traded price while preserving the locked stock row.
        stock.current_price = order.price

        await session.commit()
        return {
            "success": True,
            "shares_bought": executed_shares,
            "price_per_share": order.price,
            "total_spent": total_cost,
            "remaining_cash": buyer_company.cash
        }

    @staticmethod
    async def sell_shares(
        session: AsyncSession,
        seller_company: NatCompany,
        stock_id: int,
        shares_to_sell: int
    ) -> Dict[str, Any]:
        """Sells shares held in company portfolio to stock market orderbook."""
        if shares_to_sell <= 0:
            raise ValueError("Shares count must be positive.")

        hold_res = await session.execute(
            select(NatStockHolding).where(
                NatStockHolding.stock_id == stock_id,
                NatStockHolding.holder_company_id == seller_company.id
            )
        )
        holding = hold_res.scalar_one_or_none()
        if not holding or holding.shares_count < shares_to_sell:
            avail = holding.shares_count if holding else 0
            raise ValueError(f"Insufficient shares to sell. Required: {shares_to_sell}, Available: {avail}")

        stock = await session.scalar(
            select(NatStock).where(
                NatStock.id == stock_id,
                NatStock.is_listed == True,
            ).with_for_update()
        )
        if not stock or not stock.is_listed:
            raise ValueError("Stock is not actively listed.")

        # Sell at current market price
        total_payout = round(shares_to_sell * stock.current_price, 2)
        seller_company.cash = round(seller_company.cash + total_payout, 2)
        holding.shares_count -= shares_to_sell
        holding.updated_at = get_game_now()

        # Add sold shares back to available market float order
        order_res = await session.execute(
            select(NatStockOrder).where(
                NatStockOrder.stock_id == stock_id,
                NatStockOrder.order_type == "SELL",
                NatStockOrder.status == "ACTIVE"
            ).limit(1)
        )
        order = order_res.scalar_one_or_none()
        if order:
            order.remaining_shares += shares_to_sell
        else:
            new_ord = NatStockOrder(
                stock_id=stock_id,
                trader_company_id=seller_company.id,
                order_type="SELL",
                shares_count=shares_to_sell,
                remaining_shares=shares_to_sell,
                price=stock.current_price,
                status="ACTIVE",
                created_at=get_game_now()
            )
            session.add(new_ord)
        stock.float_shares = min(int(stock.total_shares), int(stock.float_shares) + int(shares_to_sell))

        await session.commit()
        return {
            "success": True,
            "shares_sold": shares_to_sell,
            "price_per_share": stock.current_price,
            "total_payout": total_payout,
            "remaining_shares": holding.shares_count,
            "new_cash_balance": seller_company.cash
        }
