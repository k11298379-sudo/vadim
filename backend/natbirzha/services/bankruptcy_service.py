from datetime import date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.natbirzha.config import nat_settings, get_game_today, get_game_now
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.restructuring import NatRestructuring, NatDailyFinancials
from backend.natbirzha.services.company_service import CompanyService

class BankruptcyService:
    @staticmethod
    async def file_restructuring(session: AsyncSession, company: NatCompany) -> NatRestructuring:
        if company.is_bankrupt:
            raise ValueError("Company is already undergoing restructuring.")

        now = get_game_now()
        today = get_game_today()

        # Immutable snapshot of audited NAV
        nav = await CompanyService.calculate_audited_nav(session, company)
        liquidation_pool = round(nav * nat_settings.BANKRUPTCY_LIQUIDATION_POOL_PCT, 2)  # 40%

        # Strictly next 2 real calendar dates in GAME_TIMEZONE
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=nat_settings.BANKRUPTCY_FEE_CALENDAR_DAYS)

        restructuring = NatRestructuring(
            company_id=company.id,
            snapshot_nav=nav,
            liquidation_pool=liquidation_pool,
            fee_start_date=start_date,
            fee_end_date=end_date,
            fee_rate=nat_settings.BANKRUPTCY_FEE_RATE,
            status="ACTIVE",
            created_at=now
        )
        session.add(restructuring)
        company.is_bankrupt = True

        await session.commit()
        await session.refresh(restructuring)
        return restructuring

    @staticmethod
    async def process_daily_restructuring_fee(
        session: AsyncSession,
        company: NatCompany,
        calendar_date: Optional[date] = None
    ) -> Dict[str, Any]:
        calendar_date = calendar_date or get_game_today()

        res = await session.execute(
            select(NatRestructuring).where(
                NatRestructuring.company_id == company.id,
                NatRestructuring.status == "ACTIVE"
            )
        )
        restruct = res.scalar_one_or_none()
        if not restruct:
            return {"status": "not_in_restructuring"}

        # Check if 2 calendar dates have passed
        if calendar_date > restruct.fee_end_date:
            restruct.status = "COMPLETED"
            company.is_bankrupt = False
            await session.commit()
            return {"status": "restructuring_completed", "company_id": company.id}

        # Check if currently inside fee calendar window
        if restruct.fee_start_date <= calendar_date <= restruct.fee_end_date:
            fin_res = await session.execute(
                select(NatDailyFinancials).where(
                    NatDailyFinancials.company_id == company.id,
                    NatDailyFinancials.calendar_date == calendar_date
                )
            )
            fin = fin_res.scalar_one_or_none()
            closed_profit = fin.closed_profit if fin else 0.0

            fee = 0.0
            if closed_profit > 0:
                fee = round(closed_profit * restruct.fee_rate, 2)  # 30%
                if company.cash >= fee:
                    company.cash -= fee
                    if fin:
                        fin.developer_fee_paid = fee

            await session.commit()
            return {
                "status": "fee_processed",
                "calendar_date": str(calendar_date),
                "closed_profit": closed_profit,
                "fee_deducted": fee
            }

        return {"status": "outside_fee_window"}
