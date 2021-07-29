#
# Internal status dashboards.
#

import json
import secrets
from datetime import datetime
from typing import Optional

import flask
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app
from massgov.pfml import db
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.reductions.dia import Metrics as DIAMetrics
from massgov.pfml.reductions.dua import Metrics as DUAMetrics
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
        with massgov.pfml.api.app.db_session() as db_session:
            data = process_entries(db_session)
        return flask.render_template("dashboards.html", data=data, now=utcnow())

    @app.route("/dashboard/<key>/batch/<int:batch_id>")
    def dashboard_batch_id(key, batch_id):
        if not secrets.compare_digest(key, dashboard_password):
            raise NotFound
        with massgov.pfml.api.app.db_session() as db_session:
            entry = db_session.query(ImportLog).get(batch_id)
        return flask.render_template("dashboard_batch_id.html", entry=entry, now=utcnow())

    @app.route("/dashboard/<key>/batch/<batch_name>")
    def dashboard_batch_name(key, batch_name):
        if not secrets.compare_digest(key, dashboard_password):
            raise NotFound
        with massgov.pfml.api.app.db_session() as db_session:
            data = process_entries(db_session, batch_name)
        return flask.render_template("dashboards.html", data=data, now=utcnow(), base_url="../")


def process_entries(db_session: db.Session, batch_name: Optional[str] = None) -> dict:
    data: dict = {
        "filtered": [],
        "processed": [],
    }

    entries = import_jobs_get(db_session, batch_name)

    for entry in entries:
        report = json.loads(entry.get("report")) if entry.get("report") else None
        if report and (
            report.get(DUAMetrics.DUA_PAYMENT_LISTS_DOWNLOADED_COUNT) == 0
            or report.get(DIAMetrics.DIA_PAYMENT_LISTS_DOWNLOADED_COUNT) == 0
        ):
            data["filtered"].append(entry)
        else:
            data["processed"].append(entry)
    return data


class ImportLogResponse(PydanticBaseModel):
    import_log_id: int
    source: Optional[str]
    import_type: Optional[str]
    status: Optional[str]
    report: Optional[str]
    start: Optional[datetime]
    end: Optional[datetime]


def import_jobs_get(db_session, source=None):
    query = db_session.query(ImportLog)
    if source is not None:
        query = query.filter(ImportLog.source == source)
    import_logs = query.order_by(ImportLog.import_log_id.desc()).limit(1000)

    import_logs_response = list(
        map(lambda import_log: ImportLogResponse.from_orm(import_log).dict(), import_logs,)
    )

    return import_logs_response
