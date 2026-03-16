from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_admin_user
from app.database.session import get_db
from app.modules.payment.models.payment_enum import PaymentStatusEnum
from app.modules.payment.services.payment_service import AdminPaymentService
from app.modules.users.models.user import User

admin_payment_router = APIRouter(prefix="/admin/payments", tags=["admin-payments"])


@admin_payment_router.get(
    "/",
    summary="[Admin] List all payments with filters",
    description=(
        "Retrieve **all payments** across all users.\n\n"
        "Optional query filters:\n"
        "- `user_id` — filter by a specific user\n"
        "- `status` — filter by payment status "
        "(`pending`, `succeeded`, `failed`, `refunded`)\n"
        "- `date_from` / `date_to` — filter by creation date range (ISO 8601)\n\n"
        "Returns a list of payment objects and the total count.\n\n"
        "> Requires **Admin** role (`group_id = 3`)."
    ),
    responses={
        200: {
            "description": "Payment list returned.",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "user_id": 7,
                                "order_id": 5,
                                "amount": 29.99,
                                "status": "succeeded",
                                "created_at": "2024-01-15T10:30:00Z",
                            }
                        ],
                        "total": 1,
                    }
                }
            },
        },
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "Admin access required.",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
    },
)
async def list_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[PaymentStatusEnum] = Query(
        None, description="Filter by payment status"
    ),
    date_from: Optional[datetime] = Query(
        None, description="Filter from date (ISO 8601)"
    ),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO 8601)"),
):
    payments = await AdminPaymentService.get_all_payments(
        db=db,
        user_id=user_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return {"items": payments, "total": len(payments)}
