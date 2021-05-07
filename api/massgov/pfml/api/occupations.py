import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.users.responses import OccupationResponse
from massgov.pfml.db.models.employees import LkOccupation

logger = logging.get_logger(__name__)


def occupations():
    industries = None
    with app.db_session() as db_session:
        # @todo: authentication!
        # u = get_or_404(db_session, User, user_id)

        industries = db_session.query(LkOccupation).all()

    data = [OccupationResponse.from_orm(industry).dict() for industry in industries]

    # ensure(READ, u)
    return response_util.success_response(
        message="Successfully retrieved occupations list", data=data,
    ).to_api_response()
