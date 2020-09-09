from werkzeug.exceptions import ServiceUnavailable

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)

##########################################
# Handlers
##########################################


def status_get():
    try:
        with app.db_session() as db_session:
            result = db_session.execute("SELECT 1 AS healthy").first()
            logger.warning(result)
            if result[0] != 1:
                raise Exception("Connection to DB failure")

            return response_util.success_response(message="Application healthy").to_api_response()
    except Exception:
        logger.exception("Connection to DB failure")

        return response_util.error_response(
            errors=[], status_code=ServiceUnavailable, message="Service unavailable"
        ).to_api_response()
