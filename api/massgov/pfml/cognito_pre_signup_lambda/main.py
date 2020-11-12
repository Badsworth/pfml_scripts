import massgov.pfml.cognito_pre_signup_lambda.lib as lib
import massgov.pfml.db as db
import massgov.pfml.util.logging

massgov.pfml.util.logging.init(__name__)
logger = massgov.pfml.util.logging.get_logger(__name__)

db_config = db.get_config()
db_session_raw = db.init(db_config)


def handler(event, context):
    parsed_event = lib.PreSignupEvent.parse_obj(event)
    with db.session_scope(db_session_raw, close=True) as db_session:
        response = lib.handler(db_session, parsed_event, context)

    return response.dict()
