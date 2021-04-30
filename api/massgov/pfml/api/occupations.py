import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.users.responses import OccupationResponse, OccupationTitleResponse
from massgov.pfml.db.models.employees import LkOccupation, LkOccupationTitle

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


def occupation_titles(occupation_id):
    job_titles = None
    with app.db_session() as db_session:
        # @todo: authentication!
        # u = get_or_404(db_session, User, user_id)

        job_titles = (
            db_session.query(LkOccupationTitle)
            .filter(LkOccupationTitle.occupation_id == int(occupation_id))
            .all()
        )

    data = [
        OccupationTitleResponse.from_orm(title).dict()
        for title in job_titles
        if title.occupation_title_code > 100000
    ]

    # ensure(READ, u)
    return response_util.success_response(
        message="Successfully occupation titles list", data=data,
    ).to_api_response()
