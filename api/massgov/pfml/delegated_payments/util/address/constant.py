MESSAGE_KEY = "Message"
EXPERIAN_RESULT_KEY = "experian_result"
CONFIDENCE_KEY = "Confidence"
INPUT_ADDRESS_KEY = "Input_address"
OUTPUT_ADDRESS_KEY_PREFIX = "Output_address_"
PREVIOUSLY_VERIFIED = "Previously verified"
VERIFIED = "Verification Level"
UNKNOWN = "Unknown"
FIRST_NAME = "First Name"
LAST_NAME = "Last Name"
CUSTOMER_NUMBER = "Customer Number"

MESSAGE_ALREADY_VALIDATED = "Address has already been validated"
MESSAGE_INVALID_EXPERIAN_RESPONSE = "Invalid response from Experian search API"
MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE = "Invalid response from Experian format API"
MESSAGE_VALID_ADDRESS = "Address validated by Experian"
MESSAGE_VALID_MATCHING_ADDRESS = "Matching address validated by Experian"
MESSAGE_INVALID_ADDRESS = "Address not valid in Experian"
MESSAGE_EXPERIAN_EXCEPTION_FORMAT = "An exception was thrown by Experian: {}"
MESSAGE_ADDRESS_MISSING_PART = "The address is missing a required component and cannot be validated"
CLAIMANT_ADDRESS_VALIDATION_FILENAME = "Claimant-Address-Validation-Report"
CLAIMANT_ADDRESS_VALIDATION_FILENAME_FORMAT = (
    f"%Y-%m-%d-%H-%M-%S-{CLAIMANT_ADDRESS_VALIDATION_FILENAME}"
)
CLAIMANT_ADDRESS_VALIDATION_FIELDS = [
    CUSTOMER_NUMBER,
    FIRST_NAME,
    LAST_NAME,
    INPUT_ADDRESS_KEY,
    OUTPUT_ADDRESS_KEY_PREFIX + "1",
    CONFIDENCE_KEY,
    MESSAGE_KEY,
]
TRANSACTION_FILES_SENT_COUNT = "transaction_files_sent_count"
