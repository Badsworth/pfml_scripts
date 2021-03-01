from datetime import date
from decimal import Decimal
from itertools import chain
from typing import Iterable, Optional

import pytest

from massgov.pfml.fineos.models.group_client_api import EFormAttribute
from massgov.pfml.fineos.transforms.to_fineos.base import (
    EFormAttributeBuilder,
    EFormBody,
    EFormBuilder,
)
from massgov.pfml.util.pydantic import PydanticBaseModel


class PurchaseDataAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "purchase_amount": {"name": "purchaseAmount", "type": "decimalValue"},
        "item_description": {"name": "itemDescription", "type": "stringValue"},
        "purchase_date": {"name": "purchaseDate", "type": "dateValue"},
    }

    JOINING_ATTRIBUTE = {
        "name": "PurchaseAdditionalItem",
        "type": "enumValue",
        "domainName": "PleaseSelectYesNoUnknown",
        "instanceValue": "Yes",
    }


class PurchaseData(PydanticBaseModel):
    purchase_amount: Optional[Decimal]
    item_description: Optional[str]
    purchase_date: Optional[date]


class PurchaseDataEFormBuilder(EFormBuilder):
    @classmethod
    def build(cls, purchase_data: Iterable[PurchaseData]) -> EFormBody:
        attribute_builders = map(lambda pd: PurchaseDataAttributeBuilder(pd), purchase_data)
        attributes = list(chain(cls.to_serialized_attributes(list(attribute_builders))))

        return EFormBody("Purchase Data", attributes)


@pytest.fixture
def purchase_data():
    return PurchaseData(
        purchase_amount=20, item_description="Per Week", purchase_date="2020-04-01",
    )


class TestEFormAttributeBuilder:
    def test_transform_purchase_data(self, purchase_data):
        attribute_builder = PurchaseDataAttributeBuilder(purchase_data)
        attributes = attribute_builder.to_attributes(0, "", True)
        assert len(attributes) == 3
        for r in attributes:
            assert type(r) is EFormAttribute
        (
            purchase_amount_eform_attribute,
            item_description_eform_attribute,
            purchase_date_eform_attribute,
        ) = attributes
        assert purchase_amount_eform_attribute.decimalValue == purchase_data.purchase_amount
        assert purchase_amount_eform_attribute.name == "purchaseAmount"
        assert item_description_eform_attribute.stringValue == purchase_data.item_description
        assert item_description_eform_attribute.name == "itemDescription"
        assert purchase_date_eform_attribute.dateValue == purchase_data.purchase_date
        assert purchase_date_eform_attribute.name == "purchaseDate"

    def test_transform_purchase_data_list(self, purchase_data):
        eform = PurchaseDataEFormBuilder.build([purchase_data, purchase_data])
        attributes = eform.eformAttributes
        assert len(attributes) == 7

        expected_attributes = [
            {"decimalValue": purchase_data.purchase_amount, "name": "purchaseAmount"},
            {"name": "itemDescription", "stringValue": purchase_data.item_description},
            {"dateValue": purchase_data.purchase_date.isoformat(), "name": "purchaseDate"},
            {
                "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                "name": "PurchaseAdditionalItem",
            },
            {"decimalValue": purchase_data.purchase_amount, "name": "purchaseAmount2"},
            {"name": "itemDescription2", "stringValue": purchase_data.item_description},
            {"dateValue": purchase_data.purchase_date.isoformat(), "name": "purchaseDate2"},
        ]
        assert attributes == expected_attributes
