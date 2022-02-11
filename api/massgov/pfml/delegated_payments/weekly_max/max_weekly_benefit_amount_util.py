import enum


class MaxWeeklyBenefitAmountMetrics(str, enum.Enum):
    PAYMENTS_PROCESSED_COUNT = "payments_processed_count"
    PAYMENTS_FAILED_VALIDATION_COUNT = "payments_failed_validation_count"
    PAYMENTS_PASSED_VALIDATION_COUNT = "payments_passed_validation_count"
    PAYMENT_DETAIL_MISSING_COUNT = "payment_detail_missing_count"
    PAYMENT_CAP_PAYMENT_ERROR_COUNT = "payment_cap_payment_error_count"
    PAYMENT_CAP_PAYMENT_ACCEPTED_COUNT = "payment_cap_payment_accepted_count"
    PAYMENT_SKIPPED_FOR_CAP_ADHOC_COUNT = "payment_excluded_for_cap_adhoc_count"
    MISSING_ABSENCE_PERIOD_COUNT = "missing_absence_period_count"
