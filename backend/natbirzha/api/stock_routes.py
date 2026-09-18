from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db_session
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.stocks import NatStock, NatStockHolding
from backend.natbirzha.services.auth_service import get_current_company
from backend.natbirzha.services.stock_service import StockService
from backend.natbirzha.services.dividend_service import DividendService
from backend.natbirzha.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/stocks", tags=["Natbirzha Stocks"])

class BuyStockRequest(BaseModel):
    stock_id: int
    shares_count: int = Field(gt=0)

@router.get("/market")
async def get_stocks_market(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(
        select(NatStock, NatCompany)
        .join(NatCompany, NatStock.company_id == NatCompany.id)
        .where(NatStock.is_listed == True)
    )
    stocks = [
        {
            "stock_id": s.id,
            "company_name": c.name,
            "specialization": c.specialization,
            "current_price": s.current_price,
            "total_shares": s.total_shares,
            "float_shares": s.float_shares,
            "last_valuation": s.last_valuation,
            "ipo_date": str(s.ipo_date)
        }
        for s, c in res.all()
    ]
    return {"stocks": stocks}

@router.post("/ipo/apply")
async def apply_for_ipo(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/stocks/ipo/apply", idempotency_key, {}
    )
    if cached:
        return cached[1]

    try:
        stock = await StockService.apply_for_ipo(session, company)
        resp = {
            "success": True,
            "stock_id": stock.id,
            "total_shares": stock.total_shares,
            "founder_shares": stock.founder_shares,
            "float_shares": stock.float_shares,
            "share_price": stock.current_price,
            "valuation": stock.last_valuation
        }
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/stocks/ipo/apply", idempotency_key, {}, 200, resp
        )
        return resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolio")
async def get_portfolio(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    res = await session.execute(
        select(NatStockHolding, NatStock, NatCompany)
        .join(NatStock, NatStockHolding.stock_id == NatStock.id)
        .join(NatCompany, NatStock.company_id == NatCompany.id)
        .where(NatStockHolding.holder_company_id == company.id, NatStockHolding.shares_count > 0)
    )
    holdings = [
        {
            "stock_id": h.stock_id,
            "issuer_company": c.name,
            "shares_count": h.shares_count,
            "avg_buy_price": h.avg_price,
            "current_market_price": s.current_price,
            "total_value": round(h.shares_count * s.current_price, 2)
        }
        for h, s, c in res.all()
    ]
    return {"portfolio": holdings}

@router.post("/buy")
async def buy_shares(
    req: BuyStockRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/stocks/buy", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await StockService.buy_shares(session, company, req.stock_id, req.shares_count)
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/stocks/buy", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/settle_dividends")
async def settle_dividends_endpoint(session: AsyncSession = Depends(get_db_session)):
    count = await DividendService.settle_all_public_dividends(session)
    return {"success": True, "settled_stocks_count": count}
