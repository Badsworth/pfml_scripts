import pytest

import massgov.pfml.reductions.common as reductions_common
from massgov.pfml.db.models.employees import AbsenceStatus
from massgov.pfml.db.models.factories import ClaimFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_get_claims_for_outbound(test_db_session, initialize_factories_session):
    claims_included = [
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.ADJUDICATION.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.CLOSED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.IN_REVIEW.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.IN_REVIEW.absence_status_id),
    ]

    # claims that should not be included
    [
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.INTAKE_IN_PROGRESS.absence_status_id
        ),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.DECLINED.absence_status_id),
    ]

    assert reductions_common.get_claims_for_outbound(test_db_session) == claims_included
