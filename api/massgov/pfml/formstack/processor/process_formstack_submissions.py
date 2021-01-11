import json
from typing import Optional

import smart_open

from massgov.pfml import db
from massgov.pfml.formstack.formstack_client import FormstackClient
from massgov.pfml.util.users import create_or_update_user_record


def get_form_id_from_filename(source_filename: str) -> str:
    return source_filename.split("_")[0]


def translate_form_data(submission: dict, field_data: dict) -> dict:
    return {field_data[field["field"]]["name"]: field["value"] for field in submission["data"]}


def process_formstack_submissions_file(
    db_session: db.Session,
    input_formstack: str,
    cognito_pool_id: str,
    formstack_client: Optional[FormstackClient] = None,
) -> None:
    """ Rewrite this to process CSV files; no longer working on Formstack imports directly
        TODO: https://lwd.atlassian.net/browse/EMPLOYER-613
    """

    with smart_open.open(input_formstack) as input_file:
        formstack_raw = json.load(input_file)

    if not formstack_client:
        formstack_client = FormstackClient()

    formstack_fields = formstack_client.get_fields_for_form(
        form_id=get_form_id_from_filename(input_formstack)
    )
    for raw_submission in formstack_raw:
        data = translate_form_data(submission=raw_submission, field_data=formstack_fields)
        if data["employer_identification_number_ein"]:
            cleaned_fein = data["employer_identification_number_ein"].replace("-", "").zfill(9)
        else:
            cleaned_fein = None

        create_or_update_user_record(
            db_session=db_session,
            fein=cleaned_fein,
            email=data["your_email_address"],
            cognito_pool_id=cognito_pool_id,
        )
