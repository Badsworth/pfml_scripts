import massgov.pfml.cognito_post_confirmation_lambda.lib as lib
import massgov.pfml.db as db
import massgov.pfml.util.logging

massgov.pfml.util.logging.init(__name__)
logger = massgov.pfml.util.logging.get_logger(__name__)

db_config = db.get_config()
db_session_raw = db.init(db_config)


def handler(event, context):
    try:
        parsed_event = lib.PostConfirmationEvent.parse_obj(event)
        with db.session_scope(db_session_raw, close=True) as db_session:
            response = lib.handler(db_session, parsed_event, context)
    except BaseException:
        logger.exception("Problem processing post-confirmation event")
        # all we can do at this point is show an error message by throwing an
        # exception, which isn't very useful, the user has already been
        # confirmed in the pool
        return event

    return response.dict()
