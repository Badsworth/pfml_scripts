from datetime import date

import connexion
import flask

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml import db
from massgov.pfml.api.models.common import SearchEnvelope
from massgov.pfml.db.models.applications import Holiday
from massgov.pfml.util.pydantic import PydanticBaseModel


class HolidayResponse(PydanticBaseModel):
    name: str
    date: date

    @classmethod
    def from_orm(cls, holiday: Holiday) -> "HolidayResponse":
        return HolidayResponse(name=holiday.holiday_name, date=holiday.date)


class HolidaysSearchRequestTerms(PydanticBaseModel):
    start_date: date
    end_date: date


HolidaysSearchRequest = SearchEnvelope[HolidaysSearchRequestTerms]


def get_holidays_between(start_date: date, end_date: date, db_session: db.Session) -> list[Holiday]:
    return db_session.query(Holiday).filter(Holiday.date.between(start_date, end_date)).all()


def holidays_search() -> flask.Response:
    request = HolidaysSearchRequest.parse_obj(connexion.request.json)
    with app.db_session() as db_session:
        holidays = get_holidays_between(
            request.terms.start_date, request.terms.end_date, db_session
        )

        data = [HolidayResponse.from_orm(holiday).dict() for holiday in holidays]

        return response_util.success_response(
            message="success",
            data=data,
        ).to_api_response()
