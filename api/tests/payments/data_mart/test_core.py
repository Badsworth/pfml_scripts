from datetime import date
from decimal import Decimal

import pydantic
import pytest
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.payments.data_mart.core as data_mart
import massgov.pfml.payments.payments_util as payments_util


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class MockFetchAll:
    def __init__(self, results):
        self._results = list(map(AttrDict, results))

    def fetchall(self):
        return self._results


class MockConnForFetchAll:
    def __init__(self, results):
        self._results = results

    def execute(self, *args, **kwargs):
        return MockFetchAll(self._results)

    def fetchall(self):
        return self._results


@pytest.fixture
def minimal_vendor_info_result_set():
    # no information is guaranteed from Data Mart
    db_result = {}

    parsed_result = data_mart.VendorInfoResult()

    return (db_result, parsed_result)


@pytest.fixture
def complete_vendor_info_result_set():
    db_result = {
        "vendor_customer_code": "foo",
        "vendor_active_status": Decimal("2"),
        # EFT info
        "eft_status": Decimal("6"),
        "aba_no": "123456789",
        "prenote_hold_reason": "foo",
        "prenote_requested_date": date(2020, 12, 25),
        "prenote_return_reason": "R04",
        # Address Info
        "address_id": payments_util.Constants.COMPTROLLER_AD_ID,
        "street_1": "123 MAIN ST",
        "street_2": "APT 4",
        "city": "Boston",
        "state": "MA",
        "zip_code": "12345-6789",
        "country_code": "YUG",
    }

    parsed_result = data_mart.VendorInfoResult(
        vendor_customer_code="foo",
        vendor_active_status=data_mart.VendorActiveStatus.ACTIVE,
        # EFT info
        eft_status=data_mart.EFTStatus.EFT_HOLD,
        aba_no="123456789",
        prenote_hold_reason="foo",
        prenote_requested_date=date(2020, 12, 25),
        prenote_return_reason="R04",
        # Address Info
        address_id=payments_util.Constants.COMPTROLLER_AD_ID,
        street_1="123 MAIN ST",
        street_2="APT 4",
        city="Boston",
        state="MA",
        zip_code="12345-6789",
        country_code="YUG",
    )

    return (db_result, parsed_result)


def test_get_vendor_info_no_results():
    vendor_info = data_mart.get_vendor_info(MockConnForFetchAll([]), "foo")
    assert vendor_info is None


def test_get_vendor_info_single_result_minimal(minimal_vendor_info_result_set):
    (db_record, parsed_result) = minimal_vendor_info_result_set

    vendor_info = data_mart.get_vendor_info(MockConnForFetchAll([db_record]), "foo")
    assert vendor_info == parsed_result


def test_get_vendor_info_single_result_complete(complete_vendor_info_result_set):
    (db_record, parsed_result) = complete_vendor_info_result_set

    vendor_info = data_mart.get_vendor_info(MockConnForFetchAll([db_record]), "foo")
    assert vendor_info == parsed_result


def test_get_vendor_info_multiple_results():
    with pytest.raises(MultipleResultsFound):
        data_mart.get_vendor_info(MockConnForFetchAll([{}, {}]), "foo")


def test_get_vendor_info_mangled_data(minimal_vendor_info_result_set):
    (db_record, parsed_result) = minimal_vendor_info_result_set

    db_record_bad_eft_status = db_record.copy()
    db_record_bad_eft_status["eft_status"] = "junk"

    db_record_bad_active_status = db_record.copy()
    db_record_bad_active_status["vendor_active_status"] = -42

    for bad_db_record in [db_record_bad_eft_status, db_record_bad_active_status]:
        with pytest.raises(pydantic.ValidationError):
            data_mart.get_vendor_info(
                MockConnForFetchAll([bad_db_record]), "foo",
            )
