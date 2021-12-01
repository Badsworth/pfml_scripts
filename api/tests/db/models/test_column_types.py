import pytest
from sqlalchemy import Column
from sqlalchemy.exc import StatementError
from sqlalchemy.sql.sqltypes import Integer

from massgov.pfml.db.models.base import Base
from massgov.pfml.db.models.common import FeinColumn, TaxIdColumn
from massgov.pfml.types import Fein, TaxId


class OriginalModel(Base):
    __tablename__ = "columns_to_test"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tax_id = Column(TaxIdColumn, nullable=True)
    fein = Column(FeinColumn, nullable=True)


def test_fein_tax_id_valid_columns(local_test_db_session):
    original_entry = OriginalModel(id=1, tax_id="123456789", fein="123456789")
    original_entry_two = original_entry = OriginalModel(
        id=1, tax_id=TaxId("123456789"), fein=Fein("123456789")
    )

    local_test_db_session.add(original_entry)
    local_test_db_session.add(original_entry_two)

    local_test_db_session.commit()
    original_query = local_test_db_session.query(OriginalModel).filter_by(id=1)
    original_result = original_query.one()

    assert original_result.tax_id == TaxId("123456789")
    assert original_result.fein == Fein("123456789")


def test_fein_tax_id_invalid_tax_id(local_test_db_session):
    with pytest.raises(StatementError) as err:
        original_entry = OriginalModel(id=1, tax_id="12345678912", fein="123456789")
        local_test_db_session.add(original_entry)
        local_test_db_session.commit()

    assert "does not match one of" in str(err.value)


def test_fein_tax_id_invalid_fein(local_test_db_session):
    with pytest.raises(StatementError) as err:
        original_entry = OriginalModel(id=1, tax_id="123456789", fein="12345678912")
        local_test_db_session.add(original_entry)
        local_test_db_session.commit()

    assert "does not match one of" in str(err.value)
