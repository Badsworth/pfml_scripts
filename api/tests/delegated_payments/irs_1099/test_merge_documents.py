from unittest import mock

import pytest

from massgov.pfml.db.models.factories import Pfml1099BatchFactory
from massgov.pfml.delegated_payments.irs_1099.merge_documents import Merge1099Step


@pytest.fixture
def merge_1099_document_step(test_db_session, initialize_factories_session, test_db_other_session):
    return Merge1099Step(db_session=test_db_session, log_entry_db_session=test_db_other_session)


def test_get_records_batch_as_none(merge_1099_document_step: Merge1099Step):
    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch",
        return_value=None,
    )

    with pytest.raises(
        Exception, match="Batch cannot be empty at this point.",
    ):
        merge_1099_document_step.get_record()


def test_get_records_valid_batch(merge_1099_document_step: Merge1099Step):
    batch = Pfml1099BatchFactory.create()
    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch",
        return_value=batch,
    )

    assert merge_1099_document_step.get_record() is not None


def test_merge_document_success(merge_1099_document_step: Merge1099Step):
    batch = Pfml1099BatchFactory.create()

    with mock.patch("requests.post") as mocked_post:
        mocked_post.response_value.ok = True
        mocked_post.response_value.text = "Success"

        response = merge_1099_document_step.merge_document(
            str(batch.pfml_1099_batch_id), "http://localhost:5001/api/pdf/merge"
        )
        assert response is None
