from sqlalchemy import TIMESTAMP, Column, Text
from sqlalchemy.sql.sqltypes import Integer

from massgov.pfml.db.models.base import Base, deprecated_column
from massgov.pfml.db.models.common import PostgreSQLUUID


class OriginalModel(Base):
    __tablename__ = "columns_to_deprecate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text_field = Column(Text, nullable=True)
    uuid = Column(PostgreSQLUUID)
    timestamp = Column(TIMESTAMP(timezone=True))


class DeprecatedModel(Base):
    __tablename__ = "deprecated_columns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text_field = deprecated_column(Text, nullable=True)
    uuid = deprecated_column(PostgreSQLUUID)
    timestamp = deprecated_column(TIMESTAMP(timezone=True))


def test_deprecated_column(local_test_db_session):
    original_entry = OriginalModel(id=1)
    local_test_db_session.add(original_entry)
    local_test_db_session.commit()
    original_query = local_test_db_session.query(OriginalModel).filter_by(id=1)
    original_result = original_query.one()

    assert "text_field" in original_result.__dict__.keys()
    assert "uuid" in original_result.__dict__.keys()
    assert "timestamp" in original_result.__dict__.keys()

    deprecated_entry = DeprecatedModel(id=1)
    local_test_db_session.add(deprecated_entry)
    local_test_db_session.commit()
    deprecated_query = local_test_db_session.query(DeprecatedModel).filter_by(id=1)
    deprecated_result = deprecated_query.one()

    assert "text_field" not in deprecated_result.__dict__.keys()
    assert "uuid" not in deprecated_result.__dict__.keys()
    assert "timestamp" not in deprecated_result.__dict__.keys()

    # The original implementation of deprecated_column accidentally removed the field completely. This test
    # ensures that the deprecated columns are still present if queried directly
    query_for_deprecated_field = local_test_db_session.query(DeprecatedModel.text_field).filter_by(
        id=1
    )
    result_for_deprecated_field = query_for_deprecated_field.one()

    assert "text_field" in result_for_deprecated_field.keys()
