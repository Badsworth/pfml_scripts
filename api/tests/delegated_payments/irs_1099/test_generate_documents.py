from unittest import mock

import pytest

from massgov.pfml.db.models.factories import Pfml1099BatchFactory
from massgov.pfml.delegated_payments.irs_1099.generate_documents import Generate1099DocumentsStep


@pytest.fixture
def generate_1099_document_step(
    test_db_session, initialize_factories_session, test_db_other_session
):
    return Generate1099DocumentsStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_get_records_batch_as_empty(generate_1099_document_step: Generate1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_records", return_value=[],
    )

    pfml_list = generate_1099_document_step.get_records(batch.pfml_1099_batch_id)
    assert pfml_list == []
