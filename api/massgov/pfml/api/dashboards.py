from datetime import datetime
from typing import Optional

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.util.pydantic import PydanticBaseModel


class ImportLogResponse(PydanticBaseModel):
    import_log_id: int
    source: Optional[str]
    import_type: Optional[str]
    status: Optional[str]
    report: Optional[str]
    start: Optional[datetime]
    end: Optional[datetime]


def import_jobs_get():
    with app.db_session() as db_session:
        import_logs = db_session.query(ImportLog).order_by(ImportLog.start.desc()).limit(1000)

    import_logs_response = list(
        map(lambda import_log: ImportLogResponse.from_orm(import_log).dict(), import_logs,)
    )

    return import_logs_response
