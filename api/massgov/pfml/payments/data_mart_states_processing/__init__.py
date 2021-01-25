import os

import massgov.pfml.db as pfml_db
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.util.logging as logging

from . import eft_pending, identify_mmars_status, vcc_error_report_sent, vcc_sent, vcm_report_sent

logger = logging.get_logger(__name__)


def process_all_states(pfml_db_session: pfml_db.Session) -> None:
    data_mart_client: data_mart.Client

    try:
        if os.getenv("CTR_DATA_MART_MOCK") == "true":
            data_mart_client = data_mart.TestScenariosClient(pfml_db_session)
        else:
            data_mart_client = data_mart.RealClient()
    except Exception:
        logger.exception(
            "Could not create CTR Data Mart client. Skipping processing of all dependent states."
        )
        return

    hit_exception_during_processing = False

    try:
        identify_mmars_status.process(pfml_db_session, data_mart_client)
    except Exception:
        logger.exception("Error processing 'Identify MMARS status' step")
        hit_exception_during_processing = True

    try:
        vcc_sent.process(pfml_db_session, data_mart_client)
    except Exception:
        logger.exception("Error processing 'VCC Sent' step")
        hit_exception_during_processing = True

    try:
        vcm_report_sent.process(pfml_db_session, data_mart_client)
    except Exception:
        logger.exception("Error processing 'VCM Report Sent' step")
        hit_exception_during_processing = True

    try:
        vcc_error_report_sent.process(pfml_db_session, data_mart_client)
    except Exception:
        logger.exception("Error processing 'VCC Error Report Sent' step")
        hit_exception_during_processing = True

    try:
        eft_pending.process(pfml_db_session, data_mart_client)
    except Exception:
        logger.exception("Error processing 'EFT Pending' step")
        hit_exception_during_processing = True

    if hit_exception_during_processing:
        raise Exception("One or more Data Mart processing steps hit an exception")
