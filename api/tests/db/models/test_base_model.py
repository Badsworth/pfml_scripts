from sqlalchemy import Column, Text
from sqlalchemy.sql.sqltypes import Integer

from massgov.pfml.db.models.base import Base, deprecated_column
from massgov.pfml.db.models.common import PostgreSQLUUID


class OriginalModel(Base):
    __tablename__ = "columns_to_deprecate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text_field = Column(Text, nullable=True)
    uuid = Column(PostgreSQLUUID)


class DeprecatedModel(Base):
    __tablename__ = "deprecated_columns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text_field = deprecated_column(Column(Text, nullable=True))
    uuid = deprecated_column(Column(PostgreSQLUUID))


def test_deprecated_column(local_test_db_session):
    original_entry = OriginalModel(id=1)
    local_test_db_session.add(original_entry)
    local_test_db_session.commit()
    original_query = local_test_db_session.query(OriginalModel).filter_by(id=1)
    original_result = original_query.one()

    assert "text_field" in original_result.__dict__.keys()
    assert "uuid" in original_result.__dict__.keys()

    deprecated_entry = DeprecatedModel(id=1)
    local_test_db_session.add(deprecated_entry)
    local_test_db_session.commit()
    deprecated_query = local_test_db_session.query(DeprecatedModel).filter_by(id=1)
    deprecated_result = deprecated_query.one()

    assert "text_field" not in deprecated_result.__dict__.keys()
    assert "uuid" not in deprecated_result.__dict__.keys()
