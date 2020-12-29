#
# Tests for massgov.pfml.payments.regenerate.regenerate.
#

import datetime

import freezegun
import pytest

from massgov.pfml.db.models.employees import CtrBatchIdentifier, ReferenceFile, ReferenceFileType
from massgov.pfml.payments.regenerate import gax, regenerate, vcc


@freezegun.freeze_time("2021-12-22 12:00:00")
@pytest.fixture
def regenerate_test_data(tmp_path, test_db_session):
    # Generate EOL1222VCC14 to EOL1222VCC19
    for batch in range(14, 20):
        mock_vcc_batch(batch, test_db_session, tmp_path)

    # Time is frozen for all functions that use this fixture
    with freezegun.freeze_time("2021-12-22 13:00:00"):
        yield


def mock_vcc_batch(batch, test_db_session, tmp_path):
    ctr_batch_id = CtrBatchIdentifier(
        ctr_batch_identifier="EOL1222VCC%i" % batch,
        year=2021,
        batch_date=datetime.date(2021, 12, 22),
        batch_counter=batch,
    )
    test_db_session.add(ctr_batch_id)
    test_db_session.commit()

    file_location = tmp_path / ("ready/EOL20211222VCC%i" % batch)
    reference_file = ReferenceFile(
        file_location=str(file_location),
        reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id,
        ctr_batch_identifier_id=ctr_batch_id.ctr_batch_identifier_id,
    )
    test_db_session.add(reference_file)
    test_db_session.commit()

    # The existing files are not read by the regenerate code, but need to exist.
    file_location.mkdir(parents=True)
    (file_location / ("EOL1222VCC%i.INF" % batch)).write_text("test inf file %i" % batch)
    (file_location / ("EOL1222VCC%i.DAT" % batch)).write_text("test dat file %i" % batch)


def test_regenerate_batch(tmp_path, test_db_session, regenerate_test_data):
    regenerate.regenerate_batch(2021, "EOL1222VCC14", str(tmp_path), test_db_session)

    assert (tmp_path / "error/EOL20211222VCC14/EOL1222VCC14.INF").read_text() == "test inf file 14"
    assert (tmp_path / "error/EOL20211222VCC14/EOL1222VCC14.DAT").read_text() == "test dat file 14"

    new_reference_file = (
        test_db_session.query(ReferenceFile)
        .join(CtrBatchIdentifier)
        .filter(CtrBatchIdentifier.batch_counter == 20)
        .one()
    )
    assert new_reference_file.file_location == str(tmp_path / "ready/EOL20211222VCC20")
    assert (tmp_path / "ready/EOL20211222VCC20/EOL1222VCC20.INF").is_file()
    assert (tmp_path / "ready/EOL20211222VCC20/EOL1222VCC20.DAT").is_file()

    assert new_reference_file.ctr_batch_identifier.year == 2021
    assert new_reference_file.ctr_batch_identifier.ctr_batch_identifier == "EOL1222VCC20"


def test_reference_file_by_ctr_batch(test_db_session, regenerate_test_data):
    r = regenerate.reference_file_by_ctr_batch(2021, "EOL1222VCC14", test_db_session)
    assert r.ctr_batch_identifier.ctr_batch_identifier == "EOL1222VCC14"


def test_reference_file_by_ctr_batch_not_found(test_db_session, regenerate_test_data):
    with pytest.raises(RuntimeError, match="batch 2020 EOL1222VCC14 not found in database"):
        regenerate.reference_file_by_ctr_batch(2020, "EOL1222VCC14", test_db_session)
    with pytest.raises(RuntimeError, match="batch 2021 EOL1011VCC14 not found in database"):
        regenerate.reference_file_by_ctr_batch(2021, "EOL1011VCC14", test_db_session)


def test_regenerator_class_for_reference_file(test_db_session):
    ref_file_vcc = ReferenceFile(
        file_location="payments_files/ctr/outbound/ready/EOL20211222VCC14",
        reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id,
    )
    ref_file_gax = ReferenceFile(
        file_location="payments_files/ctr/outbound/ready/EOL20211222GAX14",
        reference_file_type_id=ReferenceFileType.GAX.reference_file_type_id,
    )
    ref_file_payment = ReferenceFile(
        file_location="payments_files/ctr/outbound/ready/EOL20211222GAX14",
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
    )
    test_db_session.add(ref_file_payment)
    test_db_session.commit()

    assert regenerate.regenerator_class_for_reference_file(ref_file_vcc) == vcc.RegeneratorVCC
    assert regenerate.regenerator_class_for_reference_file(ref_file_gax) == gax.RegeneratorGAX

    with pytest.raises(RuntimeError, match=r"batch is not GAX or VCC \(type is Payment extract\)"):
        regenerate.regenerator_class_for_reference_file(ref_file_payment)
