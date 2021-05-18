import enum
import re
from typing import Any, Dict, List, Optional, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    ExperianAddressPair,
    LkState,
    Payment,
    PaymentMethod,
    State,
)
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
    PREVIOUSLY_VERIFIED = "Previously verified"
    UNKNOWN = "Unknown"

    ERROR_STATE = State.PAYMENT_FAILED_ADDRESS_VALIDATION
    SUCCESS_STATE = State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING

    MESSAGE_ALREADY_VALIDATED = "Address has already been validated"
    MESSAGE_INVALID_EXPERIAN_RESPONSE = "Invalid response from Experian search API"
    MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE = "Invalid response from Experian format API"
    MESSAGE_VALID_ADDRESS = "Address validated by Experian"
    MESSAGE_VALID_MATCHING_ADDRESS = "Matching address validated by Experian"
    MESSAGE_INVALID_ADDRESS = "Address not valid in Experian"
    MESSAGE_EXPERIAN_EXCEPTION_FORMAT = "An exception was thrown by Experian: {}"


class AddressValidationStep(Step):
    class Metrics(str, enum.Enum):
        INVALID_EXPERIAN_FORMAT = "invalid_experian_format"
        INVALID_EXPERIAN_RESPONSE = "invalid_experian_response"
        MULTIPLE_EXPERIAN_MATCHES = "multiple_experian_matches"
        NO_EXPERIAN_MATCH_COUNT = "no_experian_match_count"
        PREVIOUSLY_VALIDATED_MATCH_COUNT = "previously_validated_match_count"
        VALID_EXPERIAN_FORMAT = "valid_experian_format"
        VALIDATED_ADDRESS_COUNT = "validated_address_count"
        VERIFIED_EXPERIAN_MATCH = "verified_experian_match"

    def run_step(self) -> None:
        experian_client = _get_experian_client()

        payments = _get_payments_awaiting_address_validation(self.db_session)
        for payment in payments:
            self._validate_address_for_payment(payment, experian_client)
            self.increment(self.Metrics.VALIDATED_ADDRESS_COUNT)

        self.db_session.commit()
        return None

    def _validate_address_for_payment(self, payment: Payment, experian_client: Client) -> None:
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

        # No response
        address = address_pair.fineos_address
        try:
            response = _experian_response_for_address(experian_client, address)
        except Exception as e:
            logger.exception(
                "An exception occurred when querying the address for payment ID %s: %s"
                % (payment.payment_id, type(e).__name__)
            )

            _create_end_state_by_payment_type(
                payment=payment,
                address=address,
                address_validation_result=None,
                end_state=Constants.ERROR_STATE,
                message=Constants.MESSAGE_EXPERIAN_EXCEPTION_FORMAT.format(type(e).__name__),
                db_session=self.db_session,
            )
            self.increment("experian_search_exception_count")
            return None

        if response.result is None:
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=Constants.ERROR_STATE,
                outcome=state_log_util.build_outcome(Constants.MESSAGE_INVALID_EXPERIAN_RESPONSE),
                db_session=self.db_session,
            )
            self.increment(self.Metrics.INVALID_EXPERIAN_RESPONSE)
            return None

        result = response.result

        # Exactly one response
        if result.confidence == Confidence.VERIFIED_MATCH:
            self.increment(self.Metrics.VERIFIED_EXPERIAN_MATCH)

            formatted_address = _formatted_address_for_match(experian_client, address, result)
            if formatted_address is None:
                end_state = Constants.ERROR_STATE
                message = Constants.MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE
                self.increment(self.Metrics.INVALID_EXPERIAN_FORMAT)
            else:
                address_pair.experian_address = formatted_address
                end_state = Constants.SUCCESS_STATE
                message = Constants.MESSAGE_VALID_ADDRESS
                self.increment(self.Metrics.VALID_EXPERIAN_FORMAT)
            _create_end_state_by_payment_type(
                payment=payment,
                address=address,
                address_validation_result=result,
                end_state=end_state,
                message=message,
                db_session=self.db_session,
            )
            return None

        # Multiple responses
        if result.confidence == Confidence.MULTIPLE_MATCHES:
            self.increment(self.Metrics.MULTIPLE_EXPERIAN_MATCHES)

            end_state, message = _get_end_state_and_message_for_multiple_matches(
                result, experian_client, address_pair
            )
            _create_end_state_by_payment_type(
                payment=payment,
                address=address,
                address_validation_result=result,
                end_state=end_state,
                message=message,
                db_session=self.db_session,
            )
            return

        # Zero responses
        self.increment(self.Metrics.NO_EXPERIAN_MATCH_COUNT)
        _create_end_state_by_payment_type(
            payment=payment,
            address=address,
            address_validation_result=result,
            end_state=Constants.ERROR_STATE,
            message=Constants.MESSAGE_INVALID_EXPERIAN_RESPONSE,
            db_session=self.db_session,
        )


def _create_end_state_by_payment_type(
    payment: Payment,
    address: Address,
    address_validation_result: Optional[AddressSearchV1Result],
    end_state: LkState,
    message: str,
    db_session: db.Session,
) -> None:
    # We don't need to block ACH payments for bad addresses, but
    # still want to put it in the log so it can end up in a report
    if payment.disb_method_id != PaymentMethod.CHECK.payment_method_id:
        if end_state != Constants.ERROR_STATE:
            # Update the message to mention that for EFT we do not
            # require the address to be valid.
            message += " but not required for EFT payment"
        end_state = Constants.SUCCESS_STATE

    outcome = _outcome_for_search_result(address_validation_result, message, address)
    state_log_util.create_finished_state_log(
        associated_model=payment, end_state=end_state, outcome=outcome, db_session=db_session,
    )


def _get_experian_client() -> Client:
    return Client()


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

        try:
            return experian_format_response_to_address(client.format(key))
        except Exception as e:
            logger.exception(
                "An exception occurred when querying for the format address for key %s: %s"
                % (key, type(e).__name__)
            )

            return None

    logger.warning(
        "Experian /search endpoint did not include suggestions for Verified match",
        extra={"address_id": address.address_id},
    )
    return None


def _outcome_for_search_result(
    result: Optional[AddressSearchV1Result], msg: str, address: Address,
) -> Dict[str, Any]:

    confidence_value = (
        result.confidence.value if result and result.confidence else Constants.UNKNOWN
    )
    outcome: Dict[str, Any] = _build_experian_outcome(msg, address, confidence_value)

    if result and result.suggestions is not None:
        for i, suggestion in enumerate(result.suggestions):
            # Start list of output addresses at 1.
            label = Constants.OUTPUT_ADDRESS_KEY_PREFIX + str(1 + i)
            outcome[Constants.EXPERIAN_RESULT_KEY][label] = suggestion.text

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


# If Experian's /search endpoint returns "Multiple matches" for a given address, we attempt to find
# a "near match" and count that as the validated address in order to reduce the amount of manual
# intervention required of the Program Integrity team (https://lwd.atlassian.net/browse/PUB-145).
def _get_end_state_and_message_for_multiple_matches(
    result: AddressSearchV1Result, client: Client, address_pair: ExperianAddressPair
) -> Tuple[LkState, str]:
    address = address_pair.fineos_address
    if result.suggestions is not None:
        input_address = _normalize_address_string(
            address_to_experian_suggestion_text_format(address)
        )
        for suggestion in result.suggestions:
            # We need the global_address_key to return the formatted version of the address if we
            # find an imprecise match. If we don't have the global_address_key then we can't get the
            # formatted address so we won't even attempt to find an imprecise match.
            if (
                suggestion.text is not None
                and suggestion.global_address_key is not None
                and input_address == _normalize_address_string(suggestion.text)
            ):
                key = suggestion.global_address_key
                formatted_address = experian_format_response_to_address(client.format(key))
                address_pair.experian_address = formatted_address

                return Constants.SUCCESS_STATE, Constants.MESSAGE_VALID_MATCHING_ADDRESS

    # If there are no suggestions or no suggestions matches then we return a failure end state.
    return Constants.ERROR_STATE, Constants.MESSAGE_INVALID_ADDRESS


def _normalize_address_string(address_str: str) -> str:
    # 1. Remove space characters if they precede another space or a comma.
    # 2. Lowercase the entire address string.
    # 3. Strip leading and trailing space characters.
    return re.sub(r"\s+([\s,])", r"\1", address_str).lower().strip()
