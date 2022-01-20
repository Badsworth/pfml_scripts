import math
import re
from typing import List, Optional, Union

import pydantic
from pydantic import BaseModel

import massgov.pfml.util.logging
from massgov.pfml.api.models.claims.common import PreviousLeave
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit
from massgov.pfml.fineos.models.group_client_api import EForm
from massgov.pfml.fineos.transforms.common import (
    FineosAmountFrequencyEnum,
    FineosEmployerBenefitEnum,
)
from massgov.pfml.fineos.transforms.from_fineos.base import TransformEformAttributes

logger = massgov.pfml.util.logging.get_logger(__name__)


class EformParseError(Exception):
    """An error or validation failure when reading or parsing an EForm."""


class TransformOtherLeaveAttributes(TransformEformAttributes):
    PROP_MAP = {
        "V2OtherLeavesPastLeaveStartDate": {"name": "leave_start_date", "type": "dateValue"},
        "V2OtherLeavesPastLeaveEndDate": {"name": "leave_end_date", "type": "dateValue"},
        "V2QualifyingReason": {
            "name": "leave_reason",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
        },
        "V2LeaveFromEmployer": {
            "name": "is_for_current_employer",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
        },
        "V2Leave": {
            "name": "is_for_same_reason",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
        },
    }


class TransformConcurrentLeaveAttributes(TransformEformAttributes):
    PROP_MAP = {
        "V2AccruedStartDate": {"name": "leave_start_date", "type": "dateValue"},
        "V2AccruedEndDate": {"name": "leave_end_date", "type": "dateValue"},
        "V2AccruedPLEmployer": {
            "name": "is_for_current_employer",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
        },
    }


class TransformEmployerBenefitsAttributes(TransformEformAttributes):
    PROP_MAP = {
        "V2Amount": {"name": "benefit_amount_dollars", "type": "decimalValue"},
        "V2Frequency": {
            "name": "benefit_amount_frequency",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
            "enumOverride": FineosAmountFrequencyEnum,
        },
        "V2StartDate": {"name": "benefit_start_date", "type": "dateValue"},
        "V2EndDate": {"name": "benefit_end_date", "type": "dateValue"},
        "V2WRT": {
            "name": "benefit_type",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
            "enumOverride": FineosEmployerBenefitEnum,
        },
        "V2SalaryContinuation": {
            "name": "is_full_salary_continuous",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
            "defaultValue": None,
        },
        "V2ProgramType": {"name": "program_type", "type": "stringValue"},
    }


class TransformOtherIncomeAttributes(TransformEformAttributes):
    PROP_MAP = {
        "Amount": {"name": "benefit_amount_dollars", "type": "decimalValue"},
        "Frequency": {"name": "benefit_amount_frequency", "type": "stringValue"},
        "StartDate": {"name": "benefit_start_date", "type": "dateValue"},
        "EndDate": {"name": "benefit_end_date", "type": "dateValue"},
        "WRT": {"name": "benefit_type", "type": "enumValue", "embeddedProperty": "instanceValue"},
        "ProgramType": {
            "name": "program_type",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
        },
    }


class TransformPreviousLeaveFromOtherLeaveEform(BaseModel):
    @classmethod
    def from_fineos(cls, api_model: EForm) -> List[PreviousLeave]:
        eform = api_model.dict()
        previous_leaves = TransformOtherLeaveAttributes.list_to_props(eform["eformAttributes"])
        for leave in previous_leaves:
            leave["type"] = (
                "same_reason" if leave["is_for_same_reason"] == "Yes" else "other_reason"
            )
            if leave["is_for_current_employer"] == "Unknown":
                leave["is_for_current_employer"] = None
        try:
            return [PreviousLeave.parse_obj(leave) for leave in previous_leaves]
        except pydantic.ValidationError:
            logger.exception(
                "could not parse PreviousLeave object",
                extra={"previous_leaves": repr(previous_leaves)},
            )
            raise EformParseError("could not parse PreviousLeave object")


class TransformConcurrentLeaveFromOtherLeaveEform(BaseModel):
    @classmethod
    def from_fineos(cls, api_model: EForm) -> Optional[ConcurrentLeave]:
        eform = api_model.dict()
        concurrent_leaves = TransformConcurrentLeaveAttributes.list_to_props(
            eform["eformAttributes"]
        )
        for leave in concurrent_leaves:
            if leave["is_for_current_employer"] == "Unknown":
                leave["is_for_current_employer"] = None
        # The eform should only ever have 0 or 1 concurrent leave
        try:
            concurrent_leave = (
                ConcurrentLeave.parse_obj(concurrent_leaves[0])
                if len(concurrent_leaves) > 0
                else None
            )
        except pydantic.ValidationError:
            logger.exception(
                "could not parse ConcurrentLeave object",
                extra={"concurrent_leaves": repr(concurrent_leaves)},
            )
            raise EformParseError("could not parse ConcurrentLeave object")
        return concurrent_leave


class TransformEmployerBenefitsFromOtherIncomeEform(BaseModel):
    @classmethod
    def from_fineos(cls, api_model: EForm) -> List[EmployerBenefit]:
        eform = api_model.dict()
        benefits = TransformEmployerBenefitsAttributes.list_to_props(eform["eformAttributes"])
        return list(map(lambda benefit: EmployerBenefit.parse_obj(benefit), benefits))


class TransformOtherIncomeEform(BaseModel):
    @staticmethod
    def patch_other_income_eform(eform_obj: EForm) -> EForm:
        """
        This hack is required because Other Income Eforms from FINEOS do not follow their standard
        data format with regard to the 'WRT' field, so we patch it for them and return a valid Eform so that it
        may be transformed like other Eforms.
        Each WRT field in the form will be numbered starting with 1.
        Every even numbered field will be of value "Unknown" and can be thrown out.
        Every odd numbered field must be normalized to the normal FINEOS format which is: "WRT", "WRT2", "WRT3"...
        """
        regex = re.compile("([a-zA-Z]+)([0-9]*)")
        eform = eform_obj.dict()
        attr_name: str = ""
        attr_number: Union[int, str] = ""
        new_attrs = []
        for attr in eform["eformAttributes"]:
            matched = regex.match(attr["name"])
            attr_name, attr_number = matched.groups() if matched else (None, None)  # type: ignore
            if attr_name == "WRT" and attr_number:
                attr_number = int(attr_number)
                if attr_number % 2:
                    new_attr = {}
                    if attr_number == 1:
                        new_attr["name"] = attr_name
                    else:
                        new_attr["name"] = f"{attr_name}{str(math.ceil(attr_number / 2))}"
                    new_attr["enumValue"] = attr["enumValue"]
                    new_attrs.append(new_attr)
            else:
                new_attrs.append(attr)
        eform["eformAttributes"] = new_attrs
        return EForm.parse_obj(eform)

    @classmethod
    def from_fineos(cls, api_model: EForm) -> List[EmployerBenefit]:
        patched_eform = TransformOtherIncomeEform.patch_other_income_eform(api_model)
        eform = patched_eform.dict()
        benefits = TransformOtherIncomeAttributes.list_to_props(eform["eformAttributes"])
        return list(map(lambda benefit: EmployerBenefit.parse_obj(benefit), benefits))
