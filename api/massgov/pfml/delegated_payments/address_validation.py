import enum
from typing import Any, Dict, List, Optional, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.experian.address_validate_soap.models as sm
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    ExperianAddressPair,
    LkState,
    Payment,
    PaymentMethod,
    State,
)
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.experian.address_validate_soap.service import (
    address_to_experian_verification_search,
    experian_verification_response_to_address,
)
from massgov.pfml.experian.physical_address.service import (
    address_to_experian_suggestion_text_format,
)

logger = logging.get_logger(__name__)


class Constants:
    MESSAGE_KEY = "message"
    EXPERIAN_RESULT_KEY = "experian_result"
    CONFIDENCE_KEY = "confidence"
    INPUT_ADDRESS_KEY = "input_address"
    OUTPUT_ADDRESS_KEY_PREFIX = "output_address_"
    PREVIOUSLY_VERIFIED = "Previously verified"
    UNKNOWN = "Unknown"

    ERROR_STATE = State.PAYMENT_FAILED_ADDRESS_VALIDATION
    SUCCESS_STATE = State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK

    MESSAGE_ALREADY_VALIDATED = "Address has already been validated"
    MESSAGE_INVALID_EXPERIAN_RESPONSE = "Invalid response from Experian search API"
    MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE = "Invalid response from Experian format API"
    MESSAGE_VALID_ADDRESS = "Address validated by Experian"
    MESSAGE_VALID_MATCHING_ADDRESS = "Matching address validated by Experian"
    MESSAGE_INVALID_ADDRESS = "Address not valid in Experian"
    MESSAGE_EXPERIAN_EXCEPTION_FORMAT = "An exception was thrown by Experian: {}"
    MESSAGE_ADDRESS_MISSING_PART = (
        "The address is missing a required component and cannot be validated"
    )


class AddressValidationStep(Step):
    class Metrics(str, enum.Enum):
        EXPERIAN_SEARCH_EXCEPTION_COUNT = "experian_search_exception_count"
        INVALID_EXPERIAN_FORMAT = "invalid_experian_format"
        INVALID_EXPERIAN_RESPONSE = "invalid_experian_response"
        MULTIPLE_EXPERIAN_MATCHES = "multiple_experian_matches"
        NO_EXPERIAN_MATCH_COUNT = "no_experian_match_count"
        PREVIOUSLY_VALIDATED_MATCH_COUNT = "previously_validated_match_count"
        VALID_EXPERIAN_FORMAT = "valid_experian_format"
        VALIDATED_ADDRESS_COUNT = "validated_address_count"
        VERIFIED_EXPERIAN_MATCH = "verified_experian_match"
        ADDRESS_MISSING_COMPONENT_COUNT = "address_missing_component_count"

    def run_step(self) -> None:

        try:
            experian_soap_client = _get_experian_soap_client()

            payments = _get_payments_awaiting_address_validation(self.db_session)
            for payment in payments:
                self._validate_address_for_payment(payment, experian_soap_client)
                self.increment(self.Metrics.VALIDATED_ADDRESS_COUNT)

            self.db_session.commit()

        except Exception:
            self.db_session.rollback()
            logger.exception("Error processing addresses for payments")
            raise

        return None

    def _validate_address_for_payment(
        self, payment: Payment, experian_soap_client: soap_api.Client
    ) -> None:
        address_pair = payment.experian_address_pair

        # already validated
        if _address_has_been_validated(address_pair):
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=Constants.SUCCESS_STATE,
                outcome=_build_experian_outcome(
                    Constants.MESSAGE_ALREADY_VALIDATED,
                    cast(Address, address_pair.experian_address),
                    Constants.PREVIOUSLY_VERIFIED,
                ),
                db_session=self.db_session,
            )
            self.increment(self.Metrics.PREVIOUSLY_VALIDATED_MATCH_COUNT)

            return None

        if address_pair.fineos_address and not self._does_address_have_all_parts(
            address_pair.fineos_address
        ):
            self._create_end_state_by_payment_type(
                payment=payment,
                address=address_pair.fineos_address,
                address_validation_result=None,
                end_state=Constants.ERROR_STATE,
                message=Constants.MESSAGE_ADDRESS_MISSING_PART,
            )
            self.increment(self.Metrics.ADDRESS_MISSING_COMPONENT_COUNT)
            return None

        # When we fully switch over to using the SOAP API,
        # we can remove this check and just make it the normal behavior
        self._process_address_via_soap_api(experian_soap_client, payment, address_pair)

        return None

    def _process_address_via_soap_api(
        self,
        experian_soap_client: soap_api.Client,
        payment: Payment,
        address_pair: ExperianAddressPair,
    ) -> None:
        address = address_pair.fineos_address

        try:
            response = _experian_soap_response_for_address(experian_soap_client, address)

        except Exception as e:
            logger.exception(
                "An exception occurred when querying the address for payment ID %s: %s"
                % (payment.payment_id, type(e).__name__)
            )

            self._create_end_state_by_payment_type(
                payment=payment,
                address=address,
                address_validation_result=None,
                end_state=Constants.ERROR_STATE,
                message=Constants.MESSAGE_EXPERIAN_EXCEPTION_FORMAT.format(type(e).__name__),
            )
            self.increment(self.Metrics.EXPERIAN_SEARCH_EXCEPTION_COUNT)
            return None

        # Address was verified
        if response.verify_level == sm.VerifyLevel.VERIFIED:
            self.increment(self.Metrics.VERIFIED_EXPERIAN_MATCH)
            formatted_address = experian_verification_response_to_address(response)

            if not self._does_address_have_all_parts(address):
                end_state = Constants.ERROR_STATE
                message = Constants.MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE
                self.increment(self.Metrics.INVALID_EXPERIAN_FORMAT)

            else:
                address_pair.experian_address = formatted_address

                end_state = Constants.SUCCESS_STATE
                message = Constants.MESSAGE_VALID_ADDRESS
                self.increment(self.Metrics.VALID_EXPERIAN_FORMAT)

            self._create_end_state_by_payment_type(
                payment=payment,
                address=address,
                address_validation_result=response,
                end_state=end_state,
                message=message,
            )
            return None

        # Experian returned a non-verified scenario, all of these
        # are cases that are considered errors
        self.increment(self.Metrics.NO_EXPERIAN_MATCH_COUNT)
        self._create_end_state_by_payment_type(
            payment=payment,
            address=address,
            address_validation_result=response,
            end_state=Constants.ERROR_STATE,
            message=Constants.MESSAGE_INVALID_ADDRESS,
        )

    def _does_address_have_all_parts(self, address: Address) -> bool:
        if (
            not address.address_line_one
            or not address.city
            or not address.zip_code
            or not address.geo_state_id
        ):
            return False

        return True

    def _create_end_state_by_payment_type(
        self,
        payment: Payment,
        address: Address,
        address_validation_result: Optional[sm.SearchResponse],
        end_state: LkState,
        message: str,
    ) -> None:
        # We don't need to block ACH payments for bad addresses, but
        # still want to put it in the log so it can end up in a report
        if payment.disb_method_id != PaymentMethod.CHECK.payment_method_id:
            if end_state.state_id == Constants.ERROR_STATE.state_id:
                # Update the message to mention that for EFT we do not
                # require the address to be valid.
                message += " but not required for EFT payment"
            end_state = Constants.SUCCESS_STATE

        outcome = _outcome_for_search_result(address_validation_result, message, address)
        state_log_util.create_finished_state_log(
            associated_model=payment,
            end_state=end_state,
            outcome=outcome,
            db_session=self.db_session,
        )

        if end_state.state_id == Constants.ERROR_STATE.state_id:
            self._manage_pei_writeback_state(payment, outcome)

    def _manage_pei_writeback_state(self, payment: Payment, outcome: Dict[str, Any]) -> None:
        # Create the state log, note this is in the DELEGATED_PEI_WRITEBACK flow
        # So it is added in addition to the state log added in _create_end_state_by_payment_type
        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            outcome=outcome,
            associated_model=payment,
            db_session=self.db_session,
        )
        writeback_details = FineosWritebackDetails(
            payment=payment,
            transaction_status_id=FineosWritebackTransactionStatus.ADDRESS_VALIDATION_ERROR.transaction_status_id,
            import_log_id=cast(int, self.get_import_log_id()),
        )
        self.db_session.add(writeback_details)


def _get_experian_soap_client() -> soap_api.Client:
    return soap_api.Client()


def _get_payments_awaiting_address_validation(db_session: db.Session) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,
        db_session=db_session,
    )

    return [state_log.payment for state_log in state_logs]


def _address_has_been_validated(address_pair: ExperianAddressPair) -> bool:
    return address_pair.experian_address is not None


def _experian_soap_response_for_address(
    experian_soap_client: soap_api.Client, address: Address
) -> sm.SearchResponse:
    request = address_to_experian_verification_search(address)
    return experian_soap_client.search(request)


def _outcome_for_search_result(
    result: Optional[sm.SearchResponse], msg: str, address: Address,
) -> Dict[str, Any]:

    verify_level = (
        result.verify_level.value if result and result.verify_level else Constants.UNKNOWN
    )

    # The address passed into this is the incoming address validated.
    outcome = _build_experian_outcome(msg, address, verify_level)

    # Right now we only have the one result.
    response_address = experian_verification_response_to_address(result)
    if response_address:
        label = Constants.OUTPUT_ADDRESS_KEY_PREFIX + "1"
        outcome[Constants.EXPERIAN_RESULT_KEY][label] = address_to_experian_suggestion_text_format(
            response_address
        )

    return outcome


def _build_experian_outcome(msg: str, address: Address, confidence: str) -> Dict[str, Any]:
    outcome: Dict[str, Any] = {
        Constants.MESSAGE_KEY: msg,
        Constants.EXPERIAN_RESULT_KEY: {
            Constants.INPUT_ADDRESS_KEY: address_to_experian_suggestion_text_format(address),
            Constants.CONFIDENCE_KEY: confidence,
        },
    }
    return outcome
