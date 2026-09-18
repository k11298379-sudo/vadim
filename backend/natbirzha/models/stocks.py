from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.models import Base

class NatStock(Base):
    __tablename__ = "nat_stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_companies.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    total_shares: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    founder_shares: Mapped[int] = mapped_column(Integer, default=6000, nullable=False)
    float_shares: Mapped[int] = mapped_column(Integer, default=4000, nullable=False)
    
    current_price: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    last_valuation: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)
    is_listed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    ipo_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_spo_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NatStockHolding(Base):
    __tablename__ = "nat_stock_holdings"
    __table_args__ = (
        UniqueConstraint("stock_id", "holder_company_id", name="uq_nat_stock_holdings_stock_holder"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    holder_company_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    shares_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NatStockOrder(Base):
    __tablename__ = "nat_stock_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    trader_company_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY or SELL
    shares_count: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_shares: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NatDividend(Base):
    __tablename__ = "nat_dividends"
    __table_args__ = (
        UniqueConstraint("stock_id", "settlement_date", name="uq_nat_dividends_stock_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(Integer, ForeignKey("nat_stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    closed_profit: Mapped[float] = mapped_column(Float, nullable=False)
    dividend_pool: Mapped[float] = mapped_column(Float, nullable=False)
    per_share_amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    is_settled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
