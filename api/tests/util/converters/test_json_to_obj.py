from massgov.pfml.db.models.applications import Application
from massgov.pfml.util.converters import json_to_obj


def test_set_object_from_json():
    jsonStr = {"application_id": "123"}
    new_app = Application()
    new_app = json_to_obj.set_object_from_json(jsonStr, new_app)

    assert new_app.application_id == jsonStr["application_id"]


def test_get_json_from_object():
    new_app = Application()
    new_app.application_id = "123"

    json_str = json_to_obj.get_json_from_object(new_app)

    assert json_str["application_id"] == new_app.application_id


def test_set_object_from_empty_json():
    json_str = {}
    new_app = Application()
    new_app = json_to_obj.set_object_from_json(json_str, new_app)

    assert new_app is None


def test_get_json_from_empty_object():
    new_app = Application()
    json_str = json_to_obj.get_json_from_object(new_app)

    assert json_str == {}
