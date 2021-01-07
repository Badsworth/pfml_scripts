#
# Internal status dashboards.
#

import secrets
from datetime import datetime
from typing import Optional

import flask
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.pydantic import PydanticBaseModel


def init(app, dashboard_password):
    if dashboard_password == "":
        # Disable completely if no password is configured.
        return

    @app.route("/dashboard/<key>/batch")
    def dashboard_batch(key):
        if not secrets.compare_digest(key, dashboard_password):
            raise NotFound
        entries = import_jobs_get()
        return flask.render_template("dashboards.html", data=entries, now=utcnow())

    @app.route("/dashboard/<key>/batch/<int:batch_id>")
    def dashboard_batch_id(key, batch_id):
        if not secrets.compare_digest(key, dashboard_password):
            raise NotFound
        with massgov.pfml.api.app.db_session() as db_session:
            entry = db_session.query(ImportLog).get(batch_id)
        return flask.render_template("dashboard_batch_id.html", entry=entry, now=utcnow())


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
