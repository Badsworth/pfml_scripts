import os
import pathlib
from typing import Dict, List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import get_now
from massgov.pfml.reductions.config import get_config
from massgov.pfml.util.files import create_csv_from_list, upload_to_s3

logger = logging.get_logger(__name__)


class Constants:
    TEMPORARY_START_DATE = "20210101"
    DATE_OF_BIRTH_FORMAT = "%Y%m%d"

    CLAIMAINT_LIST_FILENAME_PREFIX = "DFML_DIA_CLAIMANTS_"
    CLAIMAINT_LIST_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"

    CASE_ID_FIELD = "CASE_ID"
    SSN_FIELD = "SSN"
    FIRST_NAME_FIELD = "FIRST_NAME"
    LAST_NAME_FIELD = "LAST_NAME"
    BIRTH_DATE_FIELD = "BIRTH_DATE"
    START_DATE_FIELD = "START_DATE"
    CLAIMAINT_LIST_FIELDS = [
        CASE_ID_FIELD,
        SSN_FIELD,
        FIRST_NAME_FIELD,
        LAST_NAME_FIELD,
        BIRTH_DATE_FIELD,
        START_DATE_FIELD,
    ]


def get_approved_claims(db_session: db.Session) -> List[Claim]:
    return (
        db_session.query(Claim)
        .filter_by(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id)
        .all()
    )


def format_employees_info_for_dia_claimant_list(approved_claims: List[Claim]) -> List[Dict]:
    approved_claims_info = []

    for claim in approved_claims:
        employee = claim.employee
        if employee is not None:
            formatted_dob = (
                employee.date_of_birth.strftime(Constants.DATE_OF_BIRTH_FORMAT)
                if employee.date_of_birth
                else ""
            )
            _info = {
                Constants.CASE_ID_FIELD: claim.fineos_absence_id,
                Constants.START_DATE_FIELD: Constants.TEMPORARY_START_DATE,
                Constants.FIRST_NAME_FIELD: employee.first_name,
                Constants.LAST_NAME_FIELD: employee.last_name,
                Constants.BIRTH_DATE_FIELD: formatted_dob,
                Constants.SSN_FIELD: employee.tax_identifier.tax_identifier.replace("-", ""),
            }

            approved_claims_info.append(_info)

    return approved_claims_info


def get_approved_claims_info_csv_path(approved_claims: List[Dict]) -> pathlib.Path:
    file_name = Constants.CLAIMAINT_LIST_FILENAME_PREFIX + get_now().strftime(
        Constants.CLAIMAINT_LIST_FILENAME_TIME_FORMAT
    )
    return create_csv_from_list(approved_claims, Constants.CLAIMAINT_LIST_FIELDS, file_name)


def create_list_of_approved_claimants(db_session: db.Session) -> None:
    config = get_config()

    # get approved claims
    approved_claims = get_approved_claims(db_session)

    # get dia info for approved claims
    dia_claimant_info = format_employees_info_for_dia_claimant_list(approved_claims)

    # get csv claimant info path
    claimant_info_path = get_approved_claims_info_csv_path(dia_claimant_info)

    # Upload info to s3
    s3_dest = os.path.join(
        config.s3_bucket, config.s3_dia_outbound_directory_path, claimant_info_path.name
    )
    upload_to_s3(str(claimant_info_path), s3_dest)

    # Update ReferenceFile and StateLog Tables
    ref_file = ReferenceFile(
        file_location=s3_dest,
        reference_file_type_id=ReferenceFileType.DIA_CLAIMANT_LIST.reference_file_type_id,
    )
    db_session.add(ref_file)
    # commit ref_file to db
    db_session.commit()

    # Update StateLog Tables
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DIA_CLAIMANT_LIST_CREATED,
        outcome=state_log_util.build_outcome("Created claimant list for DIA"),
        db_session=db_session,
    )

    # commit StateLog to db
    db_session.commit()
