import json

import pytest

from massgov.pfml.api.dashboards import process_entries
from massgov.pfml.db.models.factories import ImportLogFactory

BATCH_NAME = "DUA"


@pytest.fixture(autouse=True)
def insert_test_data(initialize_factories_session):
    ImportLogFactory(
        source="DUA", import_log_id=1, report=json.dumps({"dua_payment_lists_downloaded_count": 0})
    )
    ImportLogFactory(
        source="DUA", import_log_id=2, report=json.dumps({"dua_payment_lists_downloaded_count": 0})
    )
    ImportLogFactory(
        source="DUA", import_log_id=3, report=json.dumps({"dua_payment_lists_downloaded_count": 1})
    )
    ImportLogFactory(
        source="DIA", import_log_id=4, report=json.dumps({"dua_payment_lists_downloaded_count": 1})
    )
    ImportLogFactory(
        source="DIA", import_log_id=5, report=json.dumps({"dua_payment_lists_downloaded_count": 0})
    )
    ImportLogFactory(
        source="DIA", import_log_id=6, report=json.dumps({"dua_payment_lists_downloaded_count": 1})
    )


def test_process_entries_all_ok(test_db_session, initialize_factories_session, insert_test_data):
    data = process_entries(test_db_session)
    assert len(data["filtered"]) == 3
    assert len(data["processed"]) == 3


def test_process_entries_filtered_results(
    test_db_session, initialize_factories_session, insert_test_data
):
    data = process_entries(test_db_session, "FAKEBATCH")
    assert len(data["filtered"]) == 0
    assert len(data["processed"]) == 0


def test_process_entries_with_batch_name(
    test_db_session, initialize_factories_session, insert_test_data
):
    data = process_entries(test_db_session, BATCH_NAME)
    assert len(data["filtered"]) == 2
    assert len(data["processed"]) == 1
