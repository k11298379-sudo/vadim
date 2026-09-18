from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db_session
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.inventory import CANONICAL_ITEMS
from backend.natbirzha.services.auth_service import get_current_company
from backend.natbirzha.services.market_service import MarketService
from backend.natbirzha.services.npc_service import NPCReserveService
from backend.natbirzha.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/market", tags=["Natbirzha Market"])

class CreateOrderRequest(BaseModel):
    order_type: Optional[str] = None
    side: Optional[str] = None
    item_id: str
    price: float = Field(gt=0)
    quantity: Optional[float] = None
    amount: Optional[float] = None

class NPCTradeRequest(BaseModel):
    item_id: str
    action: Optional[str] = None
    operation: Optional[str] = None
    quantity: float = Field(gt=0)

class CancelOrderRequest(BaseModel):
    order_id: int

@router.get("/orderbook")
async def get_orderbook(
    item_id: str = Query(..., description="Item canonical ID"),
    session: AsyncSession = Depends(get_db_session)
):
    try:
        return await MarketService.get_orderbook(session, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders/create")
@router.post("/order/place")
async def create_order(
    req: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/market/orders/create", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        order_type = (req.order_type or req.side or "BUY").upper()
        qty = req.quantity if req.quantity is not None else (req.amount or 1.0)
        order = await MarketService.create_order(
            session, company, order_type, req.item_id, req.price, qty
        )
        resp = {
            "success": True,
            "order_id": order.id,
            "order_type": order.order_type,
            "item_id": order.item_id,
            "price": order.price,
            "quantity": order.quantity,
            "remaining_qty": order.remaining_qty,
            "status": order.status
        }
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/market/orders/create", idempotency_key, req.model_dump(), 200, resp
        )
        return resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, f"/api/natbirzha/market/orders/{order_id}/cancel", idempotency_key, {}
    )
    if cached:
        return cached[1]

    success = await MarketService.cancel_order(session, company, order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Active order not found or not owned by company.")

    resp = {"success": True, "cancelled_order_id": order_id}
    await IdempotencyService.save_record(
        session, company.user_id, f"/api/natbirzha/market/orders/{order_id}/cancel", idempotency_key, {}, 200, resp
    )
    return resp

@router.post("/order/cancel")
async def cancel_order_body(
    req: CancelOrderRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    return await cancel_order(req.order_id, idempotency_key, company, session)

@router.get("/npc/rates")
async def get_npc_rates():
    rates = [
        NPCReserveService.get_npc_quote(item_id)
        for item_id in CANONICAL_ITEMS.keys()
    ]
    return {"rates": rates}

@router.post("/npc/trade")
async def trade_with_npc(
    req: NPCTradeRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/market/npc/trade", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    action = (req.action or req.operation or "BUY").upper()
    res = await NPCReserveService.execute_npc_trade(
        session, company, req.item_id, action, req.quantity
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res)

    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/market/npc/trade", idempotency_key, req.model_dump(), 200, res
    )
    return res

