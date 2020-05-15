import uuid

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def uuid_gen():
    return uuid.uuid4()
