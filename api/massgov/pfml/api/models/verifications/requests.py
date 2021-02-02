from decimal import Decimal

from massgov.pfml.util.pydantic import PydanticBaseModel


class VerificationRequest(PydanticBaseModel):
    employer_id: str
    withholding_amount: Decimal
    withholding_quarter: str
