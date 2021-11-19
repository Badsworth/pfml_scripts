from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from pydantic import BaseModel, Extra, Field

import massgov.pfml.reductions.dia as dia
from massgov.pfml.db.models.employees import AbsenceStatus, Claim, DiaReductionPayment


class DFMLReportRow(BaseModel):
    # all the raw data from DIA
    customer_number: str = Field(..., alias=dia.Constants.CUSTOMER_NUMBER_FIELD)
    board_no: Optional[str] = Field(None, alias=dia.Constants.BOARD_NO_FIELD)
    event_id: Optional[str] = Field(None, alias=dia.Constants.EVENT_ID)
    event_description: Optional[str] = Field(None, alias=dia.Constants.INS_FORM_OR_MEET_FIELD)
    eve_created_date: Optional[date] = Field(None, alias=dia.Constants.EVE_CREATED_DATE_FIELD)
    event_occurrence_date: Optional[date] = Field(
        None, alias=dia.Constants.FORM_RECEIVED_OR_DISPOSITION_FIELD
    )
    award_id: Optional[str] = Field(None, alias=dia.Constants.AWARD_ID_FIELD)
    award_code: Optional[str] = Field(None, alias=dia.Constants.AWARD_CODE_FIELD)
    award_amount: Optional[Decimal] = Field(None, alias=dia.Constants.AWARD_AMOUNT_FIELD)
    award_date: Optional[date] = Field(None, alias=dia.Constants.AWARD_DATE_FIELD)
    start_date: Optional[date] = Field(None, alias=dia.Constants.START_DATE_FIELD)
    end_date: Optional[date] = Field(None, alias=dia.Constants.END_DATE_FIELD)
    weekly_amount: Optional[Decimal] = Field(None, alias=dia.Constants.WEEKLY_AMOUNT_FIELD)
    award_created_date: Optional[date] = Field(None, alias=dia.Constants.AWARD_CREATED_DATE_FIELD)
    termination_date: Optional[date] = Field(None, alias=dia.Constants.TERMINATION_DATE_FIELD)

    # with additional data about existing claims
    absence_case_id: Optional[str] = Field(None, alias=dia.Constants.ABSENCE_CASE_ID)
    absence_period_start_date: Optional[date] = Field(
        None, alias=dia.Constants.ABSENCE_PERIOD_START_DATE
    )
    absence_period_end_date: Optional[date] = Field(
        None, alias=dia.Constants.ABSENCE_PERIOD_END_DATE
    )
    absence_case_status: Optional[str] = Field(None, alias=dia.Constants.ABSENCE_CASE_STATUS)

    class Config:
        allow_population_by_field_name = True
        extra = Extra.forbid


DFMLReportRowData = Tuple[DiaReductionPayment, Optional[Claim]]


def make_report_row_from_payment(row_data: DFMLReportRowData) -> DFMLReportRow:
    payment, claim = row_data

    row = DFMLReportRow(
        customer_number=payment.fineos_customer_number,
        board_no=payment.board_no,
        event_id=payment.event_id,
        event_description=payment.event_description,
        eve_created_date=payment.eve_created_date,
        event_occurrence_date=payment.event_occurrence_date,
        award_id=payment.award_id,
        award_code=payment.award_code,
        award_amount=payment.award_amount,
        award_date=payment.award_date,
        start_date=payment.start_date,
        end_date=payment.end_date,
        weekly_amount=payment.weekly_amount,
        award_created_date=payment.award_created_date,
        termination_date=payment.termination_date,
    )

    if claim:
        row.absence_case_id = claim.fineos_absence_id
        row.absence_period_start_date = claim.absence_period_start_date
        row.absence_period_end_date = claim.absence_period_end_date
        row.absence_case_status = (
            AbsenceStatus.get_description(claim.fineos_absence_status_id)
            if claim.fineos_absence_status_id
            else None
        )

    return row
