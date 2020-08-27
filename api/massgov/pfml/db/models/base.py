import datetime
import uuid

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def uuid_gen():
    return uuid.uuid4()


def utc_timestamp_gen():
    """ Generate a tz-aware timestamp pinned to UTC """
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
