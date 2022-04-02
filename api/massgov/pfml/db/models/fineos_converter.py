import datetime
from typing import Any

from massgov.pfml.fineos.models.customer_api import (
    ChangeRequestPeriod,
    ChangeRequestReason,
    LeavePeriodChangeRequest,
)


# That's better! Now all the FINEOS conversion code lives here, and the db model classes can
# optionally include this mixin in order to access the "to_fineos_model" method. We can then
# expand the "to_fineos_model" method to handle more db model classes.
#
#
# ...But wait, what's this?
# We have a cyclic dependency! :(
# The db_model package imports this mixin, and the mixin needs to import the db_model
# in order to reference the ChangeRequest class...
#
# We can hack around this by NOT importing the ChangeRequest class, but
# this is gross for a number of reasons. We would have to hardcode a string
# in order to switch based on the class of the calling object. Boo!
# On top of that, the actual converter methods won't know what kind of object
# they're operating on! They just take a generic, un-typed "self", and hope
# that the object they're working with behaves as expected. Not ideal, and will
# make this code hard to read if it expands to include 10+ FINEOS converter methods.
#
# Is there some way to modularize this code without introducing a cyclic dependency?
# Maybe we can extend the db_model class so that it contains more class features...
class FineosModelConverter:
    def to_fineos_model(self) -> Any:
        if "massgov.pfml.db.models.employees.ChangeRequest" in str(type(self)):
            return self._to_leave_period_change_request()
        else:
            # unable to convert class
            raise Exception

    # Throws a pydantic.error_wrappers.ValidationError if startDate or endDate are None
    def _to_leave_period_change_request(self) -> LeavePeriodChangeRequest:
        claim = self.claim
        change_request_type = self.type

        is_withdrawal = change_request_type == "Withdrawal"
        if is_withdrawal:
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

        is_medical_to_bonding = change_request_type == "Medical To Bonding Transition"
        if is_medical_to_bonding:
            return LeavePeriodChangeRequest(
                reason=ChangeRequestReason(fullId=0, name="Add time for different Absence Reason"),
                additionalNotes="Medical to bonding transition",
                changeRequestPeriods=[
                    ChangeRequestPeriod(startDate=self.start_date, endDate=self.end_date)
                ],
            )

        is_extension = (
            self.end_date is not None
            and claim.absence_period_end_date is not None
            and self.end_date > claim.absence_period_end_date
        )
        if is_extension:
            return LeavePeriodChangeRequest(
                reason=ChangeRequestReason(fullId=0, name="Add time for identical Absence Reason"),
                additionalNotes="Extension",
                changeRequestPeriods=[
                    ChangeRequestPeriod(startDate=self.start_date, endDate=self.end_date)
                ],
            )

        is_cancellation = (
            self.end_date is not None
            and claim.absence_period_end_date is not None
            and self.end_date < claim.absence_period_end_date
        )
        if is_cancellation:
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
        else:
            raise ValueError(
                f"Unable to convert ChangeRequest to FINEOS model - Unknown type: {change_request_type}"
            )
