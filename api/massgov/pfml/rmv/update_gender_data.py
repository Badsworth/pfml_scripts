import os
from dataclasses import asdict, dataclass
from datetime import date
from typing import List, Optional, cast

import pydantic

import massgov.pfml.rmv.errors as rmv_errors
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.config import RMVAPIBehavior
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import Claim, Employee, Gender, TaxIdentifier
from massgov.pfml.rmv.caller import MockZeepCaller
from massgov.pfml.rmv.client import RmvClient, is_mocked
from massgov.pfml.rmv.models import RmvAcknowledgement, RMVSex, VendorLicenseInquiryRequest
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)

rmv_sex_to_gender = {
    RMVSex.M: Gender.MAN,
    RMVSex.F: Gender.WOMAN,
    RMVSex.X: Gender.NONBINARY,
}


@dataclass
class UpdateGenderDataReport:
    total_claimants_count: int = 0
    claimants_updated_count: int = 0
    claimants_errored_count: int = 0
    claimants_skipped_count: int = 0
    status: Optional[str] = None


@background_task("update-gender-data-from-rmv")
def main():
    """ECS handler function."""
    with db.session_scope(db.init(), close=True) as db_session:
        logger.info(
            "Getting the list of claimants we want to update with gender data from the RMV API.",
        )
        claimants_to_scrape = get_claimants_to_scrape(db_session)
        logger.info("Starting gender data update.",)

        rmv_mocking_behavior = RMVAPIBehavior(
            str(os.environ.get("RMV_API_BEHAVIOR", RMVAPIBehavior.MOCK.value))
        )
        if rmv_mocking_behavior is not RMVAPIBehavior.MOCK:
            rmv_client = RmvClient()
        else:
            rmv_client = RmvClient(MockZeepCaller())

        report = update_gender_data(
            db_session, rmv_client, rmv_mocking_behavior, claimants_to_scrape
        )
        logger.info(
            "Finished gender data update.", extra={"report": asdict(report)},
        )


def update_gender_data(
    db_session: db.Session,
    rmv_client: RmvClient,
    rmv_mocking_behavior: RMVAPIBehavior,
    claimants_to_scrape: List[Employee],
) -> UpdateGenderDataReport:
    report = UpdateGenderDataReport()
    report.total_claimants_count = len(claimants_to_scrape)

    for claimant in claimants_to_scrape:
        vendor_license_inquiry_request = VendorLicenseInquiryRequest(
            first_name=claimant.first_name,
            last_name=claimant.last_name,
            date_of_birth=cast(date, claimant.date_of_birth),
            ssn_last_4=str(cast(TaxIdentifier, claimant.tax_identifier).tax_identifier_last4),
        )

        # We will skip any mocked calls to the RMV API when running this script.
        # For testing purposes, a mock RmvClient can be passed into this function, with rmv_mocking_behavior
        # set accordingly.
        if is_mocked(rmv_mocking_behavior, claimant.first_name, claimant.last_name):
            report.claimants_skipped_count += 1
            continue

        try:
            license_inquiry_response = rmv_client.vendor_license_inquiry(
                vendor_license_inquiry_request
            )
        except rmv_errors.RmvUnknownError:
            report.claimants_errored_count += 1
            logger.exception(
                "An unknown error occurred within the RMV API",
                extra={"employee_id": claimant.employee_id},
            )
            break
        except pydantic.ValidationError:
            report.claimants_errored_count += 1
            logger.exception(
                "Could not parse response from the RMV API.",
                extra={"employee_id": claimant.employee_id},
            )
            continue

        if isinstance(license_inquiry_response, RmvAcknowledgement):
            report.claimants_errored_count += 1
            logger.warning(
                "Unable to retrieve record from RMV API for this claimant.",
                extra={
                    "employee_id": claimant.employee_id,
                    "error": license_inquiry_response.value,
                },
            )
            continue

        if not isinstance(license_inquiry_response.sex, RMVSex):
            report.claimants_errored_count += 1
            logger.warning(
                "Unexpected value for gender",
                extra={
                    "employee_id": claimant.employee_id,
                    "gender_value": license_inquiry_response.sex,
                },
            )
            continue

        claimant.gender_id = rmv_sex_to_gender[license_inquiry_response.sex].gender_id
        report.claimants_updated_count += 1
        logger.info(
            "Claimant gender data updated successfully.",
            extra={"employee_id": claimant.employee_id},
        )

    db_session.commit()

    # check whether or not all claimants were processed
    if (
        report.claimants_updated_count
        + report.claimants_errored_count
        + report.claimants_skipped_count
        == report.total_claimants_count
    ):
        status = "Gender data update completed successfully."
    else:
        status = "Gender data update terminated early."

    report.status = status
    return report


def get_claimants_to_scrape(db_session: db.Session) -> List[Employee]:
    # We only want claimants that don't currently have gender data. Claimants without a DOB or who we know don't have
    # a state id will not be in the RMV API, so we can exclude those claimants.

    claimants = (
        db_session.query(Employee)
        .join(Claim)
        .outerjoin(Application)
        .filter(Employee.gender_id.is_(None))
        .filter(Employee.date_of_birth.isnot(None))
        .filter(Employee.tax_identifier_id.isnot(None))
        .filter(Application.has_state_id.isnot(False))
        .all()
    )

    return claimants
