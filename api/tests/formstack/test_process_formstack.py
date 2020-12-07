import json
import pathlib

import pytest

from massgov.pfml.formstack.processor.process_formstack_submissions import (
    get_form_id_from_filename,
    translate_form_data,
)

TEST_FOLDER = pathlib.Path(__file__).parent


def load_file(file_path):
    with open(file_path) as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def tpa_form_fields():
    return load_file(TEST_FOLDER / "3973485_form_fields.json")


@pytest.fixture(scope="session")
def la_form_fields():
    return load_file(TEST_FOLDER / "3969371_form_fields.json")


@pytest.fixture(scope="session")
def la_form_subs():
    return load_file(TEST_FOLDER / "3969371_mock_subs.json")


@pytest.fixture(scope="session")
def tpa_form_subs():
    return load_file(TEST_FOLDER / "3973485_mock_subs.json")


@pytest.fixture
def mock_formstack_la(la_form_fields):
    class MockFormstackClient:
        def get_fields_for_form(self, *args, **kwargs):
            return la_form_fields

    return MockFormstackClient()


class TestProcessFormstackSubmissions:
    def test_form_id_from_filename(self):
        assert (
            get_form_id_from_filename("2345_2020_01_01_00_00_00_2020_02_01_00_00_0.json") == "2345"
        )

    def test_translate_tpa_form_data(self, tpa_form_fields, tpa_form_subs):
        translated = translate_form_data(tpa_form_subs[0], field_data=tpa_form_fields)
        assert set(translated.keys()) == set(
            [
                "upload_list_of_companies_you_represent",
                "verification_code",
                "your_email_address",
                "your_name",
            ]
        )
        expected = {
            "upload_list_of_companies_you_represent": "https://www.jenkins.com/",
            "verification_code": "C8S7LQ",
            "your_email_address": "michaellogan@yahoo.com",
            "your_name": "Meagan Hartman",
        }
        assert translated == expected

    def test_translate_la_form_data(self, la_form_fields, la_form_subs):
        translated = translate_form_data(la_form_subs[0], field_data=la_form_fields)

        assert set(translated.keys()) >= set(
            [
                "employer_identification_number_ein",
                "verification_code",
                "your_email_address",
                "your_name",
            ]
        )
        expected = {
            "employer_identification_number_ein": "446973469",
            "verification_code": "NQPH4M",
            "your_email_address": "hernandezjeremy@klein.com",
            "your_name": "Nicholas Smith",
        }
        for k, v in expected.items():
            assert translated[k] == v
