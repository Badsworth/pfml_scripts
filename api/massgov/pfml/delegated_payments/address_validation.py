from typing import Any, Dict, List, Optional, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Address, Employee, ExperianAddressPair, Payment, State
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.experian.physical_address.client import Client
from massgov.pfml.experian.physical_address.client.models.search import (
    AddressSearchV1Request,
    AddressSearchV1Response,
    AddressSearchV1Result,
    Confidence,
)
from massgov.pfml.experian.physical_address.service import (
    address_to_experian_search_request,
    address_to_experian_suggestion_text_format,
    experian_format_response_to_address,
)

logger = logging.get_logger(__name__)


class Constants:
    MESSAGE_KEY = "message"
    EXPERIAN_RESULT_KEY = "experian_result"
    CONFIDENCE_KEY = "confidence"
    INPUT_ADDRESS_KEY = "input_address"
    OUTPUT_ADDRESS_KEY_PREFIX = "output_address_"


class AddressValidationStep(Step):
    def run_step(self) -> None:
        experian_client = _get_experian_client()

        employees = _get_employees_awaiting_address_validation(self.db_session)
        for employee in employees:
            self._validate_address_for_employee(employee, experian_client)

        payments = _get_payments_awaiting_address_validation(self.db_session)
        for payment in payments:
            self._validate_address_for_payment(payment, experian_client)

        self.db_session.commit()
        return None

    def _validate_address_for_employee(self, employee: Employee, experian_client: Client) -> None:
        address_pair = cast(ExperianAddressPair, employee.experian_address_pair)
        if _address_has_been_validated(address_pair):
            state_log_util.create_finished_state_log(
                associated_model=employee,
                end_state=State.DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS,
                outcome=state_log_util.build_outcome("Address has already been validated"),
                db_session=self.db_session,
            )
            return None

        address = address_pair.fineos_address
        response = _experian_response_for_address(experian_client, address)
        if response.result is None:
            state_log_util.create_finished_state_log(
                associated_model=employee,
                end_state=State.CLAIMANT_FAILED_ADDRESS_VALIDATION,
                outcome=state_log_util.build_outcome("Invalid response from Experian search API"),
                db_session=self.db_session,
            )
            return None

        result = response.result
        if result.confidence != Confidence.VERIFIED_MATCH:
            outcome = _outcome_for_search_result(result, "Address not valid in Experian", address)
            state_log_util.create_finished_state_log(
                associated_model=employee,
                end_state=State.CLAIMANT_FAILED_ADDRESS_VALIDATION,
                outcome=outcome,
                db_session=self.db_session,
            )
            return None

        formatted_address = _formatted_address_for_match(experian_client, address, result)
        if formatted_address is None:
            state_log_util.create_finished_state_log(
                associated_model=employee,
                end_state=State.CLAIMANT_FAILED_ADDRESS_VALIDATION,
                outcome=state_log_util.build_outcome("Invalid response from Experian format API"),
                db_session=self.db_session,
            )
            return None

        address_pair.experian_address = formatted_address
        outcome = _outcome_for_search_result(result, "Address validated by Experian", address)
        state_log_util.create_finished_state_log(
            associated_model=employee,
            end_state=State.DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS,
            outcome=outcome,
            db_session=self.db_session,
        )
        return None

    def _validate_address_for_payment(self, payment: Payment, experian_client: Client) -> None:
        address_pair = cast(ExperianAddressPair, payment.claim.employee.experian_address_pair)
        if _address_has_been_validated(address_pair):
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
                outcome=state_log_util.build_outcome("Address has already been validated"),
                db_session=self.db_session,
            )
            return None

        address = address_pair.fineos_address
        response = _experian_response_for_address(experian_client, address)
        if response.result is None:
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
                outcome=state_log_util.build_outcome("Invalid response from Experian search API"),
                db_session=self.db_session,
            )
            return None

        result = response.result
        if result.confidence != Confidence.VERIFIED_MATCH:
            outcome = _outcome_for_search_result(result, "Address not valid in Experian", address)
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
                outcome=outcome,
                db_session=self.db_session,
            )
            return None

        formatted_address = _formatted_address_for_match(experian_client, address, result)
        if formatted_address is None:
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
                outcome=state_log_util.build_outcome("Invalid response from Experian format API"),
                db_session=self.db_session,
            )
            return None

        address_pair.experian_address = formatted_address
        outcome = _outcome_for_search_result(result, "Address validated by Experian", address)
        state_log_util.create_finished_state_log(
            associated_model=payment,
            end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            outcome=outcome,
            db_session=self.db_session,
        )
        return None


def _get_experian_client() -> Client:
    return Client()


def _get_employees_awaiting_address_validation(db_session: db.Session) -> List[Employee]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.CLAIMANT_READY_FOR_ADDRESS_VALIDATION,
        db_session=db_session,
    )

    return [state_log.employee for state_log in state_logs]


def _get_payments_awaiting_address_validation(db_session: db.Session) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,
        db_session=db_session,
    )

    return [state_log.payment for state_log in state_logs]


def _address_has_been_validated(address_pair: ExperianAddressPair) -> bool:
    return address_pair.experian_address is not None


def _experian_response_for_address(client: Client, address: Address) -> AddressSearchV1Response:
    request_formatted_address: AddressSearchV1Request = address_to_experian_search_request(address)
    return client.search(request_formatted_address)


def _formatted_address_for_match(
    client: Client, address: Address, result: AddressSearchV1Result
) -> Optional[Address]:
    if result.suggestions is not None and len(result.suggestions) > 0:
        key = result.suggestions[0].global_address_key
        if key is None:
            logger.warning(
                "Experian /search endpoint did not include global_address_key with response for Verified match",
                extra={"address_id": address.address_id},
            )
            return None

        return experian_format_response_to_address(client.format(key))

    logger.warning(
        "Experian /search endpoint did not include suggestions for Verified match",
        extra={"address_id": address.address_id},
    )
    return None


def _outcome_for_search_result(
    result: AddressSearchV1Result, msg: str, address: Address
) -> Dict[str, Any]:
    outcome: Dict[str, Any] = {
        Constants.MESSAGE_KEY: msg,
        Constants.EXPERIAN_RESULT_KEY: {
            Constants.INPUT_ADDRESS_KEY: address_to_experian_suggestion_text_format(address),
            Constants.CONFIDENCE_KEY: result.confidence,
        },
    }

    if result.suggestions is not None:
        for i, suggestion in enumerate(result.suggestions):
            # Start list of output addresses at 1.
            label = Constants.OUTPUT_ADDRESS_KEY_PREFIX + str(1 + i)
            outcome[Constants.EXPERIAN_RESULT_KEY][label] = suggestion.text

    return outcome
