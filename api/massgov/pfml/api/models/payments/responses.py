from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import UUID4, parse_obj_as

from massgov.pfml.db.models.employees import PaymentDetails
from massgov.pfml.util.pydantic import PydanticBaseModel


class PaymentLineResponse(PydanticBaseModel):
    payment_line_id: UUID4
    amount: Decimal
    line_type: str


class PaymentDetailsResponse(PydanticBaseModel):
    payment_details_id: UUID4
    period_start_date: Optional[date]
    period_end_date: Optional[date]
    net_amount: Decimal
    gross_amount: Decimal
    payment_lines: list[PaymentLineResponse]

    @classmethod
    def from_orm(cls, payment_details: PaymentDetails) -> "PaymentDetailsResponse":
        return PaymentDetailsResponse(
            payment_details_id=payment_details.payment_details_id,
            period_start_date=payment_details.period_start_date,
            period_end_date=payment_details.period_end_date,
            net_amount=payment_details.amount,
            gross_amount=payment_details.business_net_amount,
            # PaymentDetails.payment_lines is defined as a backfill relationship on PaymentLine
            payment_lines=parse_obj_as(List[PaymentLineResponse], payment_details.payment_lines),  # type: ignore
        )


class PaymentResponse(PydanticBaseModel):
    payment_id: Optional[UUID4]
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
    payment_details: list[PaymentDetailsResponse]
