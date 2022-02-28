import pytest

from massgov.pfml.api.models.claims.responses import (
    AbsencePeriodResponse,
    ClaimForPfmlCrmResponse,
    ClaimResponse,
)
from massgov.pfml.db.models.absences import AbsencePeriodType
from massgov.pfml.db.models.factories import AbsencePeriodFactory, ClaimFactory
from tests.helpers.api_responses import assert_structural_subset


@pytest.mark.parametrize(
    "input_period_type_id, output_period_type",
    [
        (
            AbsencePeriodType.CONTINUOUS.absence_period_type_id,
            AbsencePeriodType.CONTINUOUS.absence_period_type_description,
        ),
        (
            AbsencePeriodType.INTERMITTENT.absence_period_type_id,
            AbsencePeriodType.INTERMITTENT.absence_period_type_description,
        ),
        (
            AbsencePeriodType.REDUCED_SCHEDULE.absence_period_type_id,
            AbsencePeriodType.REDUCED_SCHEDULE.absence_period_type_description,
        ),
        (
            AbsencePeriodType.EPISODIC.absence_period_type_id,
            AbsencePeriodType.INTERMITTENT.absence_period_type_description,
        ),
        (
            AbsencePeriodType.TIME_OFF_PERIOD.absence_period_type_id,
            AbsencePeriodType.CONTINUOUS.absence_period_type_description,
        ),
    ],
)
def test_absence_period_types_from_orm(
    input_period_type_id, output_period_type, initialize_factories_session
):
    absence_period_record = AbsencePeriodFactory.create(absence_period_type_id=input_period_type_id)
    response = AbsencePeriodResponse.from_orm(absence_period_record)

    assert response.period_type == output_period_type


def test_response_structural_subset(initialize_factories_session):
    claim = ClaimFactory.create()
    service_now_response = ClaimForPfmlCrmResponse.from_orm(claim).dict()
    full_response = ClaimResponse.from_orm(claim).dict()

    assert_structural_subset(service_now_response, full_response)
