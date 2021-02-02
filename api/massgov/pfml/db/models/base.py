import uuid
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.ext.declarative import as_declarative

from massgov.pfml.util.datetime import utcnow


@as_declarative()
class Base:
    def dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def for_json(self):
        json_valid_dict = {}
        dictionary = self.dict()
        for key, value in dictionary.items():
            if isinstance(value, UUID) or isinstance(value, Decimal):
                json_valid_dict[key] = str(value)
            elif isinstance(value, date) or isinstance(value, datetime):
                json_valid_dict[key] = value.isoformat()
            else:
                json_valid_dict[key] = value

        return json_valid_dict


def uuid_gen():
    return uuid.uuid4()


def utc_timestamp_gen():
    """ Generate a tz-aware timestamp pinned to UTC """
    return utcnow()
