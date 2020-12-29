#
# Tests for massgov.pfml.payments.regenerate.regenerate.
#

import datetime
import uuid

import pytest

import massgov.pfml.payments.regenerate.regenerate
from massgov.pfml.db.models.employees import ReferenceFileType, CtrBatchIdentifier, ReferenceFile
from massgov.pfml.db.models.factories import CtrBatchIdentifierFactory, ReferenceFileFactory


@pytest.fixture
def regenerate_data(test_db_session, initialize_factories_session):
    ctr_batch_id = CtrBatchIdentifier(
        ctr_batch_identifier="EOL1222VCC14",
        year=2021,
        batch_date=datetime.date(2021, 12, 22),
        batch_counter=14,
    )
    test_db_session.add(ctr_batch_id)
    test_db_session.commit()

    reference_file = ReferenceFile(
        file_location="payments_files/ctr/outbound/ready/EOL20211222VCC14",
        reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id,
        ctr_batch_identifier_id=ctr_batch_id.ctr_batch_identifier_id,
    )
    test_db_session.add(reference_file)
    test_db_session.commit()


def test_regenerate_batch(tmp_path, test_db_session):
    massgov.pfml.payments.regenerate.regenerate.regenerate_batch("a", tmp_path, test_db_session)


def test_reference_file_by_ctr_batch(test_db_session, regenerate_data):
    r = massgov.pfml.payments.regenerate.regenerate.reference_file_by_ctr_batch(
        "EOL1222VCC14", test_db_session
    )
    assert r.file_location == "payments_files/ctr/outbound/ready/EOL20211222VCC14"
    assert r.ctr_batch_identifier.ctr_batch_identifier == "EOL1222VCC14"
