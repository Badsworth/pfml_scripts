from enum import Enum

from massgov.pfml.api.models.common import PreviousLeaveQualifyingReason

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


# Used to convert between the API's PreviousLeaveQualifyingReason enums and FINEOS' QualifyingReasons eform enum
class OtherLeaveEFormQualifyingReason(FineosToApiEnumConverter):
    PREGNANCY_MATERNITY = "Pregnancy"
    SERIOUS_HEALTH_CONDITION = "An illness or injury"
    CARE_FOR_A_FAMILY_MEMBER = "Caring for a family member with a serious health condition"
    CHILD_BONDING = "Bonding with my child after birth or placement"
    MILITARY_CAREGIVER = "Caring for a family member who serves in the armed forces"
    MILITARY_EXIGENCY_FAMILY = (
        "Managing family affairs while a family member is on active duty in the armed forces"
    )
    UNKNOWN = "Unknown"

    @staticmethod
    def get_api_enum():
        return PreviousLeaveQualifyingReason
