import pytest

from massgov.pfml.api.models.claims.responses import AbsencePeriodResponse
from massgov.pfml.db.models.absences import AbsencePeriodType
from massgov.pfml.db.models.factories import AbsencePeriodFactory


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
