import uuid
import os
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import inspect, Column
from sqlalchemy.ext.declarative import as_declarative
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from alembic_utils.replaceable_entity import register_entities

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


def deprecated(column: Column):
    """ Simple utility for deprecating a column. """
    column.type.should_evaluate_none = True
    return deferred(column)


def renamed_to(table_name: str, name: str, column_name: str, column: Column):
    schema = os.getenv("DB_SCHEMA", "public")
    signature = f"copy_{table_name}_{column_name}_{name}"
    table = f"{schema}.{table_name}"

    bidirectional_copy_fn = PGFunction(
        schema=schema,
        signature=f"{signature}()",
        definition=f"""
        RETURNS TRIGGER AS $func$
        BEGIN
            IF NEW.{name} IS NULL THEN
                NEW.{name} := NEW.{column_name};
            ELSIF NEW.{column_name} IS NULL THEN
                NEW.{column_name} := NEW.{name};
            END IF;
            RETURN NEW;
        END $func$ LANGUAGE plpgsql
        """
    )

    trigger = PGTrigger(
        schema=schema,
        signature=signature,
        on_entity=table,
        definition=f"""
        BEFORE INSERT OR UPDATE ON {table}
        FOR EACH ROW
        WHEN (NEW.{name} IS NULL OR NEW.{column_name} IS NULL)
        EXECUTE FUNCTION {signature}()
        """
    )

    register_entities([bidirectional_copy_fn, trigger])
