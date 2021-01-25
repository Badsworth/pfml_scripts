import uuid

from sqlalchemy.ext.declarative import declarative_base

from massgov.pfml.util.datetime import utcnow

Base = declarative_base()


def uuid_gen():
    return uuid.uuid4()


def utc_timestamp_gen():
    """ Generate a tz-aware timestamp pinned to UTC """
    return utcnow()
