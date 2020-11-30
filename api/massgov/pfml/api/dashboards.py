#
# Internal status dashboards.
#

import secrets
from datetime import datetime
from typing import Optional

import flask
import flask_httpauth

import massgov.pfml.api.app
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.pydantic import PydanticBaseModel


def init(app, dashboard_password):
    auth = flask_httpauth.HTTPBasicAuth(realm="PFML dashboards")

    if dashboard_password == "":
        # Disable completely if no password is configured.
        return

    @auth.verify_password
    def verify_password(username, password):
        if username == "pfmlapi" and secrets.compare_digest(password, dashboard_password):
            return username
        return None  # Not authorized

    @app.route("/dashboards", methods=["GET"])
    @auth.login_required
    def serve_dashboard():
        entries = import_jobs_get()
        return flask.render_template("dashboards.html", data=entries, now=utcnow())


class ImportLogResponse(PydanticBaseModel):
    import_log_id: int
    source: Optional[str]
    import_type: Optional[str]
    status: Optional[str]
    report: Optional[str]
    start: Optional[datetime]
    end: Optional[datetime]


def import_jobs_get():
    with massgov.pfml.api.app.db_session() as db_session:
        import_logs = (
            db_session.query(ImportLog).order_by(ImportLog.import_log_id.desc()).limit(1000)
        )

    import_logs_response = list(
        map(lambda import_log: ImportLogResponse.from_orm(import_log).dict(), import_logs,)
    )

    return import_logs_response
