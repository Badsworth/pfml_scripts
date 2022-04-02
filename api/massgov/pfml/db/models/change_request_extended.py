import datetime
from api.massgov.pfml.db.models.fineos_converter import FineosModelConverter

from massgov.pfml.fineos.models.customer_api import (
    ChangeRequestPeriod,
    ChangeRequestReason,
    LeavePeriodChangeRequest,
)

from .employees import ChangeRequest as DBModel
from .employees import ChangeRequestType


# Now we're in business!
# This ChangeRequest class behaves exactly like the db_model class, but also includes
# the `to_fineos_model` method.
#
# The dependency is one-directional, and doesn't require any changes in the db_model class
#
# Some cool stuff:
# * This class can be used interchangeably with the db model class
# * We could move a lot of the helper methods in the db_models file into these classes,
#   which will allow the db_model module file to focus exclusively on the fields stored
#   in the db
# * This pattern can also be used to introduce `to_api_response` and `from_api_request` methods!
# 
# Gotchas:
# * Until this is widely adopted, it just introduces yet another pattern that will be used
#   inconsistently
# * Anything that checks against the explicit type of the ChangeRequest class will need to
#   know which of the two classes to expect
class ChangeRequest(DBModel):
    ...

    # TODO: use a mixin, leave the methods abstract, and override them in the extended model
    # TODO: some examples of how this is used
    # can we do db interactions with it? save, read, etc
    # when we query from the db, can we get these instead?
    # is the linter happy?
    # 

    # TODO: static
    # TODO: could call some validations
    def from_api_request():
        return None

    # Throws a pydantic.error_wrappers.ValidationError if startDate or endDate are None
    def to_fineos_model(self) -> LeavePeriodChangeRequest:
        claim = self.claim
        change_request_type = self.type

        is_withdrawal = change_request_type == ChangeRequestType.WITHDRAWAL.description
        if is_withdrawal:
            return self._convert_change_request_withdrawal(claim)

        is_medical_to_bonding = (
            change_request_type == ChangeRequestType.MEDICAL_TO_BONDING.description
        )
        if is_medical_to_bonding:
            return self._convert_change_request_medical_to_bonding()

        is_extension = (
            self.end_date is not None
            and claim.absence_period_end_date is not None
            and self.end_date > claim.absence_period_end_date
        )
        if is_extension:
            return self._convert_change_request_extension()

        is_cancellation = (
            self.end_date is not None
            and claim.absence_period_end_date is not None
            and self.end_date < claim.absence_period_end_date
        )
        if is_cancellation:
            return self._convert_change_request_cancellation(claim)
        else:
            raise ValueError(
                f"Unable to convert ChangeRequest to FINEOS model - Unknown type: {change_request_type}"
            )
    
    def _convert_change_request_withdrawal(self, claim) -> LeavePeriodChangeRequest:
        # A withdrawal removes all dates from a claim
        return LeavePeriodChangeRequest(
            reason=ChangeRequestReason(fullId=0, name="Employee Requested Removal"),
            additionalNotes="Withdrawal",
            changeRequestPeriods=[
                ChangeRequestPeriod(
                    startDate=claim.absence_period_start_date,
                    endDate=claim.absence_period_end_date,
                )
            ],
        )

    def _convert_change_request_medical_to_bonding(self) -> LeavePeriodChangeRequest:
        return LeavePeriodChangeRequest(
            reason=ChangeRequestReason(fullId=0, name="Add time for different Absence Reason"),
            additionalNotes="Medical to bonding transition",
            changeRequestPeriods=[
                ChangeRequestPeriod(startDate=self.start_date, endDate=self.end_date)
            ],
        )

    def _convert_change_request_extension(self) -> LeavePeriodChangeRequest:
        return LeavePeriodChangeRequest(
            reason=ChangeRequestReason(fullId=0, name="Add time for identical Absence Reason"),
            additionalNotes="Extension",
            changeRequestPeriods=[
                ChangeRequestPeriod(startDate=self.start_date, endDate=self.end_date)
            ],
        )

    def _convert_change_request_cancellation(self, claim) -> LeavePeriodChangeRequest:
            assert self.end_date

            # In FINEOS, a cancellation means you are removing time.
            # So the date range represents the dates that will be removed from leave
            return LeavePeriodChangeRequest(
                reason=ChangeRequestReason(fullId=0, name="Employee Requested Removal"),
                additionalNotes="Cancellation",
                changeRequestPeriods=[
                    ChangeRequestPeriod(
                        startDate=self.end_date + datetime.timedelta(days=1),
                        endDate=claim.absence_period_end_date,
                    )
                ],
            )
