import hashlib
import json
from typing import Optional, Tuple, Dict, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.natbirzha.models.idempotency import NatIdempotencyRecord

class IdempotencyService:
    @staticmethod
    def compute_payload_hash(payload: Any) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    async def check_or_conflict(
        cls,
        session: AsyncSession,
        user_id: int,
        endpoint: str,
        idempotency_key: str,
        payload: Any
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        if not idempotency_key:
            return None

        req_hash = cls.compute_payload_hash(payload)
        res = await session.execute(
            select(NatIdempotencyRecord).where(
                NatIdempotencyRecord.user_id == user_id,
                NatIdempotencyRecord.endpoint == endpoint,
                NatIdempotencyRecord.idempotency_key == idempotency_key
            )
        )
        record = res.scalar_one_or_none()
        if not record:
            return None

        if record.request_hash == req_hash:
            # Same key, identical payload -> return cached response
            return record.status_code, record.response_body
        else:
            # Same key, different payload -> HTTP 409 Conflict
            raise HTTPException(
                status_code=409,
                detail="Idempotency key reused with different payload."
            )

    @classmethod
    async def save_record(
        cls,
        session: AsyncSession,
        user_id: int,
        endpoint: str,
        idempotency_key: str,
        payload: Any,
        status_code: int,
        response_body: Dict[str, Any]
    ) -> None:
        if not idempotency_key:
            return

        req_hash = cls.compute_payload_hash(payload)
        record = NatIdempotencyRecord(
            user_id=user_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=req_hash,
            status_code=status_code,
            response_body=response_body
        )
        session.add(record)
        await session.commit()
