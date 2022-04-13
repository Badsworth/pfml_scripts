from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import UUID4

from massgov.pfml.util.pydantic import PydanticBaseModel


class PaymentResponse(PydanticBaseModel):
    payment_id: Optional[UUID4]
    fineos_c_value: str
    fineos_i_value: str
    period_start_date: date
    period_end_date: date
    amount: Optional[Decimal]
    sent_to_bank_date: Optional[date]
    payment_method: str
    expected_send_date_start: Optional[date]
    expected_send_date_end: Optional[date]
    cancellation_date: Optional[date]
    status: str
    writeback_transaction_status: Optional[str]
    transaction_date: Optional[date]
    transaction_date_could_change: bool
