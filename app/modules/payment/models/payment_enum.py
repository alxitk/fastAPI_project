from enum import Enum


class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"
