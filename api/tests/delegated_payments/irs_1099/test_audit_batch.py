import pytest

import massgov.pfml.delegated_payments.irs_1099.audit_batch as audit_batch
import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
from massgov.pfml.delegated_payments.mock.irs_1099_factory import Pfml1099Factory


@pytest.fixture
def audit_batch_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return audit_batch.AuditBatchStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_audit_batch(audit_batch_step, local_test_db_session):

    # Create batch records for test
    Pfml1099Factory(db_session=local_test_db_session).get_or_create_batch()

    year = pfml_1099_util.get_tax_year()

    # Get the counts before running
    before_batch_counts = pfml_1099_util.get_batch_counts(local_test_db_session)

    # Run the step
    audit_batch_step.run()
    after_batch_counts = pfml_1099_util.get_batch_counts(local_test_db_session)

    # We should have one more batch
    assert after_batch_counts[year] == before_batch_counts[year] + 1
