from datetime import date
from decimal import Decimal
from enum import Enum
from itertools import chain
from typing import Iterable, Optional

import pytest

from massgov.pfml.fineos.transforms.to_fineos.base import (
    EFormAttributeBuilder,
    EFormBody,
    EFormBuilder,
)
from massgov.pfml.util.pydantic import PydanticBaseModel


class ItemCategory(str, Enum):
    HARDWARE = "Hardware"
    BOOKS = "Books"
    FOOD = "Refreshments"


class ShoppingCategory(str, Enum):
    HARDWARE = "Home improvement"
    BOOKS = "Books"
    FOOD = "Food"


class PurchaseDataAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "purchase_amount": {"name": "purchaseAmount", "type": "decimalValue"},
        "item_description": {"name": "itemDescription", "type": "stringValue"},
        "purchase_date": {"name": "purchaseDate", "type": "dateValue"},
        "item_category": {"name": "itemCategory", "type": "enumValue", "domainName": "category"},
        "shopping_category": {
            "name": "shoppingCategory",
            "type": "enumValue",
            "domainName": "shopping",
            "enumOverride": ShoppingCategory,
        },
    }


class PurchaseData(PydanticBaseModel):
    purchase_amount: Optional[Decimal]
    item_description: Optional[str]
    purchase_date: Optional[date]
    item_category: Optional[ItemCategory]
    shopping_category: Optional[ItemCategory]


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
        item_category=ItemCategory.HARDWARE,
        shopping_category=ItemCategory.HARDWARE,
    )


class TestEFormBuilder:
    def test_purchase_data_eform_builder(self, purchase_data):
        eform = PurchaseDataEFormBuilder.build([purchase_data, purchase_data])
        attributes = eform.eformAttributes
        assert len(attributes) == 10

        expected_attributes = [
            {"decimalValue": purchase_data.purchase_amount, "name": "purchaseAmount"},
            {"name": "itemDescription", "stringValue": purchase_data.item_description},
            {"dateValue": purchase_data.purchase_date.isoformat(), "name": "purchaseDate"},
            {
                "name": "itemCategory",
                "enumValue": {"domainName": "category", "instanceValue": "Hardware"},
            },
            {
                "name": "shoppingCategory",
                "enumValue": {"domainName": "shopping", "instanceValue": "Home improvement"},
            },
            {"decimalValue": purchase_data.purchase_amount, "name": "purchaseAmount2"},
            {"name": "itemDescription2", "stringValue": purchase_data.item_description},
            {"dateValue": purchase_data.purchase_date.isoformat(), "name": "purchaseDate2"},
            {
                "name": "itemCategory2",
                "enumValue": {"domainName": "category", "instanceValue": "Hardware"},
            },
            {
                "name": "shoppingCategory2",
                "enumValue": {"domainName": "shopping", "instanceValue": "Home improvement"},
            },
        ]
        assert attributes == expected_attributes

    def test_data_with_none_string(self, purchase_data):
        purchase_data.item_description = None

        eform = PurchaseDataEFormBuilder.build([purchase_data])

        attributes = eform.eformAttributes
        assert len(attributes) == 4

        item_description_attr = eform.get_attribute("itemDescription")
        assert item_description_attr is None

    def test_data_with_none_enum(self, purchase_data):
        purchase_data.item_category = None

        eform = PurchaseDataEFormBuilder.build([purchase_data])

        attributes = eform.eformAttributes
        assert len(attributes) == 4

        item_category_attr = eform.get_attribute("itemCategory")
        assert item_category_attr is None
