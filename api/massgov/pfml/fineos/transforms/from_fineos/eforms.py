import math
import re
from typing import List, Union

from pydantic import BaseModel

from massgov.pfml.api.models.claims.common import PreviousLeave
from massgov.pfml.api.models.common import EmployerBenefit
from massgov.pfml.fineos.models.group_client_api import EForm
from massgov.pfml.fineos.transforms.from_fineos.base import TransformEformAttributes


class TransformOtherLeaveAttributes(TransformEformAttributes):
    PROP_MAP = {
        "BeginDate": {"name": "leave_start_date", "type": "dateValue"},
        "EndDate": {"name": "leave_end_date", "type": "dateValue"},
        "QualifyingReason": {
            "name": "leave_reason",
            "type": "enumValue",
            "embeddedProperty": "instanceValue",
        },
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


class TransformOtherLeaveEform(BaseModel):
    @classmethod
    def from_fineos(cls, api_model: EForm) -> List[PreviousLeave]:
        eform = api_model.dict()
        leaves = TransformOtherLeaveAttributes.list_to_props(eform["eformAttributes"])
        return list(map(lambda leave: PreviousLeave.parse_obj(leave), leaves))


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
