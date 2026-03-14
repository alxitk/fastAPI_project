from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_admin_user
from app.database.session import get_db
from app.modules.payment.models.payment_enum import PaymentStatusEnum
from app.modules.payment.services.payment_service import AdminPaymentService
from app.modules.users.models.user import User

admin_payment_router = APIRouter(prefix="/admin/payments", tags=["admin-payments"])


@admin_payment_router.get("/")
async def list_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    user_id: Optional[int] = Query(None),
    status: Optional[PaymentStatusEnum] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    payments = await AdminPaymentService.get_all_payments(
        db=db,
        user_id=user_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return {"items": payments, "total": len(payments)}
