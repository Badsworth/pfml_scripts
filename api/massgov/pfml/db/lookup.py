#
# Classes for handling database lookup tables.
#

from typing import Any, Dict

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


class LookupTable:
    """Representation of a database lookup table.

    Usage looks like this::

        class Shape(lookup.LookupTable):
            # Model class, which must have an __init__ that matches the below code
            model = LkShape

            # Column names, primary key first, then description, and any other columns last
            column_names = ("shape_id", "name", "corners")

            # Template model instances (transient, never saved to database directly)
            CIRCLE = LkShape(1, "circle", 0)
            SQUARE = LkShape(2, "square", 4)
            TRIANGLE = LkShape(3, "triangle", 3)

    Once created, it is always safe to add rows. Updating or removing rows must be done with
    caution as other tables may refer to the lookup table. Row ids can not be changed.

    Use the sync_to_database() method to add or update rows in the database to match the template
    instances. Rows will not be removed.

    Attributes of the template model instances can be used directly safely and without a database
    session::

        shape_id = Shape.SQUARE.shape_id

    They can not be used as relationships as they are transient (not linked to a db session)::

        # Will cause an error on commit
        widget.shape = Shape.CIRCLE

    Instead use the get_instance() method to get an instance merged into a db session::

        widget.shape = Shape.get_instance(db_session, template=Shape.CIRCLE)
        widget.shape = Shape.get_instance(db_session, description="triangle")

    To get an id dynamically from a description, use the get_id() method, which does not require a
    db session::

        shape_id = Shape.get_id("square")
    """

    model: Any = None
    column_names: tuple = ()
    # Map from template model instance (specified in the class declaration) to persistent or
    # detached model instance.
    template_instance_to_db_instance: Dict[type, type] = {}
    # Map from description (2nd column) to persistent or detached model instance.
    description_to_db_instance: Dict[str, type] = {}

    @classmethod
    def repr(cls):
        return "LookupTable(%s, %s)" % (cls.model.__qualname__, cls.model.__table__.name)

    @classmethod
    def sync_to_database(cls, db_session):
        """Synchronize the lookup table to a database by adding or updating rows if needed.

        Should be called once during process initialization.

        In test cases, called once per temporary database schema."""
        row_update_count = 0
        for key, value in vars(cls).items():
            if not isinstance(value, cls.model):
                continue
            if cls.sync_row_to_database(db_session, key, value):
                row_update_count += 1
        logger.info("%s: row update count %i", cls.repr(), row_update_count)
        return row_update_count

    @classmethod
    def sync_row_to_database(cls, db_session, key, template_instance):
        """Synchronize a single row of the lookup table to a database by adding or updating it."""
        row = tuple(map(template_instance.__getattribute__, cls.column_names))
        row_id, description = row[0], row[1]
        row_was_updated = False
        instance = db_session.query(cls.model).get(row_id)
        if instance is None:
            instance = db_session.merge(template_instance)
            logger.info("%s: add %s %r", cls.repr(), key, row)
            row_was_updated = True
        else:
            existing_values = tuple(map(instance.__getattribute__, cls.column_names))
            if row != existing_values:
                instance = db_session.merge(template_instance)
                row_was_updated = True
                logger.info("%s: update %s %r", cls.repr(), key, row)
        cls.template_instance_to_db_instance[template_instance] = instance
        cls.description_to_db_instance[description] = instance
        return row_was_updated

    @classmethod
    def get_instance(cls, db_session, template=None, description=None):
        """Get an ORM instance for the row by template instance or description.

        The instance is merged into the given db session.
        """
        if template is not None and description is None:
            if not isinstance(template, cls.model):
                raise TypeError("template must be of type %r" % cls.model)
            if template not in cls.template_instance_to_db_instance:
                raise ValueError("template not an attribute or called before sync")
            return db_session.merge(cls.template_instance_to_db_instance[template], load=False)
        elif template is None and description is not None:
            return db_session.merge(cls.description_to_db_instance[description], load=False)
        else:
            raise TypeError("either template or description must be passed")

    @classmethod
    def get_id(cls, description):
        """Get the id for the row by description."""
        return getattr(cls.description_to_db_instance[description], cls.column_names[0])
