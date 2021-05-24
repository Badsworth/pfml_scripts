from datetime import date
from decimal import Decimal
from itertools import chain
from typing import Iterable, Optional

import pytest

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
        "item_category": {"name": "itemCategory", "type": "enumValue", "domainName": "category"},
    }

    JOINING_ATTRIBUTE = {
        "name": "PurchaseAdditionalItem",
        "type": "enumValue",
        "domainName": "PleaseSelectYesNoUnknown",
        "instanceValue": "Yes",
    }

    STATIC_ATTRIBUTES = [
        {
            "name": "PurchaseType",
            "type": "enumValue",
            "domainName": "PleaseSelectCreditChequeCash",
            "instanceValue": "Credit",
        },
        {"name": "ApiVersion", "type": "decimalValue", "instanceValue": 1.0,},
    ]


class PurchaseData(PydanticBaseModel):
    purchase_amount: Optional[Decimal]
    item_description: Optional[str]
    purchase_date: Optional[date]
    item_category: Optional[str]


class PurchaseDataEFormBuilder(EFormBuilder):
    @classmethod
    def build(cls, purchase_data: Iterable[PurchaseData]) -> EFormBody:
        attribute_builders = map(lambda pd: PurchaseDataAttributeBuilder(pd), purchase_data)
        attributes = list(chain(cls.to_serialized_attributes(list(attribute_builders))))

        return EFormBody("Purchase Data", attributes)


@pytest.fixture
def purchase_data():
    return PurchaseData(
        purchase_amount=20,
        item_description="Per Week",
        purchase_date="2020-04-01",
        item_category="Hardware",
    )


class TestEFormBuilder:
    def test_purchase_data_eform_builder(self, purchase_data):
        eform = PurchaseDataEFormBuilder.build([purchase_data, purchase_data])
        attributes = eform.eformAttributes
        assert len(attributes) == 13

        expected_attributes = [
            {"decimalValue": purchase_data.purchase_amount, "name": "purchaseAmount"},
            {"name": "itemDescription", "stringValue": purchase_data.item_description},
            {"dateValue": purchase_data.purchase_date.isoformat(), "name": "purchaseDate"},
            {
                "name": "itemCategory",
                "enumValue": {"domainName": "category", "instanceValue": "Hardware"},
            },
            {
                "enumValue": {
                    "domainName": "PleaseSelectCreditChequeCash",
                    "instanceValue": "Credit",
                },
                "name": "PurchaseType",
            },
            {"decimalValue": 1.0, "name": "ApiVersion"},
            {
                "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                "name": "PurchaseAdditionalItem",
            },
            {"decimalValue": purchase_data.purchase_amount, "name": "purchaseAmount2"},
            {"name": "itemDescription2", "stringValue": purchase_data.item_description},
            {"dateValue": purchase_data.purchase_date.isoformat(), "name": "purchaseDate2"},
            {
                "name": "itemCategory2",
                "enumValue": {"domainName": "category", "instanceValue": "Hardware"},
            },
            {
                "enumValue": {
                    "domainName": "PleaseSelectCreditChequeCash",
                    "instanceValue": "Credit",
                },
                "name": "PurchaseType2",
            },
            {"decimalValue": 1.0, "name": "ApiVersion2"},
        ]
        assert attributes == expected_attributes

    def test_data_with_none_string(self, purchase_data):
        purchase_data.item_description = None

        eform = PurchaseDataEFormBuilder.build([purchase_data])

        attributes = eform.eformAttributes
        assert len(attributes) == 5

        item_description_attr = eform.get_attribute("itemDescription")
        assert item_description_attr is None

    def test_data_with_none_enum(self, purchase_data):
        purchase_data.item_category = None

        eform = PurchaseDataEFormBuilder.build([purchase_data])

        attributes = eform.eformAttributes
        assert len(attributes) == 5

        item_category_attr = eform.get_attribute("itemCategory")
        assert item_category_attr is None
