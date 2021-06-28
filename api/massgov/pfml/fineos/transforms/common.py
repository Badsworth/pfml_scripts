from enum import Enum

from massgov.pfml.api.models.applications.common import OtherIncomeType
from massgov.pfml.api.models.common import AmountFrequency, EmployerBenefitType

# Value used for unexpected FINEOS enum values
DEFAULT_ENUM_REPLACEMENT_VALUE = "Unknown"


class FineosToApiEnumConverter(str, Enum):
    @staticmethod
    def get_api_enum():
        raise Exception("Not implemented")

    @classmethod
    # Given a FINEOS enum value will return the corresponding API enum value. If the FINEOS
    # enum value isn't one that we expect then will return 'Unknown'.
    def to_api_enum(cls, value: str) -> str:
        # Return the default enum value if we get an unexpected value
        if value not in [member.value for name, member in cls.__members__.items()]:
            return DEFAULT_ENUM_REPLACEMENT_VALUE

        # Otherwise map the fineos enum value to the corresponding API enum value
        fineos_enum = cls(value)
        return fineos_enum.get_api_enum()[fineos_enum.name]


# Convert between the API's OtherIncomeType enum and FINEOS' WageReplacementType2 eform enum
class FineosOtherIncomeEnum(FineosToApiEnumConverter):
    workers_comp = "Workers Compensation"
    unemployment = "Unemployment Insurance"
    ssdi = "Social Security Disability Insurance"
    retirement_disability = (
        "Disability benefits under a governmental retirement plan such as STRS or PERS"
    )
    jones_act = "Jones Act benefits"
    railroad_retirement = "Railroad Retirement benefits"
    other_employer = "Earnings from another employer or through self-employment"

    @staticmethod
    def get_api_enum():
        return OtherIncomeType


# Convert between the API's EmployerBenefitType enum and FINEOS' WageReplacementType eform enum
class FineosEmployerBenefitEnum(FineosToApiEnumConverter):
    short_term_disability = "Temporary disability insurance (Long- or Short-term)"
    permanent_disability_insurance = "Permanent disability insurance"
    family_or_medical_leave_insurance = "Family or medical leave, such as a parental leave policy"
    unknown = "Unknown"

    @staticmethod
    def get_api_enum():
        return EmployerBenefitType


# Convert between the API's AmountFrequency enum and FINEOS' FrequencyEforms eform enum
class FineosAmountFrequencyEnum(FineosToApiEnumConverter):
    per_day = "Per Day"
    per_week = "Per Week"
    per_month = "Per Month"
    all_at_once = "One Time / Lump Sum"
    unknown = "Not Provided"

    @staticmethod
    def get_api_enum():
        return AmountFrequency
