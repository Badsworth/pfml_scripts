from datetime import date
from decimal import Decimal
from typing import Optional

import pytest

from massgov.pfml.fineos.models.group_client_api import EFormAttribute, ModelEnum
from massgov.pfml.fineos.transforms.to_fineos.base import TransformEformAttributes
from massgov.pfml.util.pydantic import PydanticBaseModel


class TransformPurchaseData(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "purchase_amount": {"name": "purchaseAmount", "type": "decimalValue"},
        "item_description": {"name": "itemDescription", "type": "stringValue"},
        "purchase_date": {"name": "purchaseDate", "type": "dateValue"},
    }

    ADDITIONAL_OBJECT = EFormAttribute(
        name="PurchaseAdditionalItem",
        enumValue=ModelEnum(domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"),
    )


class PurchaseData(PydanticBaseModel):
    purchase_amount: Optional[Decimal]
    item_description: Optional[str]
    purchase_date: Optional[date]


@pytest.fixture
def purchase_data():
    return PurchaseData(
        purchase_amount=20, item_description="Per Week", purchase_date="2020-04-01",
    )


class TestTransformEformAttributes:
    def test_transform_purchase_data(self, purchase_data):
        transformed = TransformPurchaseData.to_attributes(purchase_data)
        assert len(transformed) == 3
        for r in transformed:
            assert type(r) is EFormAttribute
        (
            purchase_amount_eform_attribute,
            item_description_eform_attribute,
            purchase_date_eform_attribute,
        ) = transformed
        assert purchase_amount_eform_attribute.decimalValue == purchase_data.purchase_amount
        assert purchase_amount_eform_attribute.name == "purchaseAmount"
        assert item_description_eform_attribute.stringValue == purchase_data.item_description
        assert item_description_eform_attribute.name == "itemDescription"
        assert purchase_date_eform_attribute.dateValue == purchase_data.purchase_date.strftime(
            "%Y-%m-%d"
        )
        assert purchase_date_eform_attribute.name == "purchaseDate"

    def test_transform_purchase_data_list(self, purchase_data):
        transformed = TransformPurchaseData.list_to_attributes([purchase_data, purchase_data])
        assert len(transformed) == 7
        (
            purchase_amount_eform_attribute,
            item_description_eform_attribute,
            purchase_date_eform_attribute,
            purchase_amount_eform_attribute2,
            item_description_eform_attribute2,
            purchase_date_eform_attribute2,
            addition_object_eform_attribute2,
        ) = transformed
        assert purchase_amount_eform_attribute.decimalValue == purchase_data.purchase_amount
        assert purchase_amount_eform_attribute.name == "purchaseAmount"
        assert item_description_eform_attribute.stringValue == purchase_data.item_description
        assert item_description_eform_attribute.name == "itemDescription"
        assert purchase_date_eform_attribute.dateValue == purchase_data.purchase_date.strftime(
            "%Y-%m-%d"
        )
        assert purchase_date_eform_attribute.name == "purchaseDate"
        assert purchase_amount_eform_attribute2.decimalValue == purchase_data.purchase_amount
        assert purchase_amount_eform_attribute2.name == "purchaseAmount2"
        assert item_description_eform_attribute2.stringValue == purchase_data.item_description
        assert item_description_eform_attribute2.name == "itemDescription2"
        assert purchase_date_eform_attribute2.dateValue == purchase_data.purchase_date.strftime(
            "%Y-%m-%d"
        )
        assert purchase_date_eform_attribute2.name == "purchaseDate2"
        assert addition_object_eform_attribute2.enumValue == ModelEnum(
            domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"
        )
        assert addition_object_eform_attribute2.name == "PurchaseAdditionalItem2"
