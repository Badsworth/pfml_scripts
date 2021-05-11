#
# Tests for massgov.pfml.db.lookup.
#

import pytest
import sqlalchemy.orm.exc
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

import massgov.pfml.db.lookup as lookup
from massgov.pfml.db.models.base import Base

# every test in here requires real resources
pytestmark = pytest.mark.integration


# A lookup table with an id and description.
class LkColour(Base):
    __tablename__ = "lk_colour__lookup_test"
    colour_id = Column(Integer, primary_key=True, autoincrement=True)
    colour_name = Column(Text, nullable=False)

    def __init__(self, colour_id, name):
        self.colour_id = colour_id
        self.colour_name = name

    def __repr__(self):
        return "<LkColour(colour_id=%r, colour_name=%r)>" % (self.colour_id, self.colour_name)


# A lookup table with an id, description, and another column.
class LkShape(Base):
    __tablename__ = "lk_shape__lookup_test"
    shape_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    corners = Column(Integer, nullable=False)

    def __init__(self, shape_id, name, corners):
        self.shape_id = shape_id
        self.name = name
        self.corners = corners

    def __repr__(self):
        return "<LkShape(shape_id=%r, name=%r, corners=%r)>" % (
            self.shape_id,
            self.name,
            self.corners,
        )


# A lookup table with an id and description.
class LkPolygon(Base):
    __tablename__ = "lk_polygon__lookup_test"
    polygon_id = Column(Integer, primary_key=True, autoincrement=True)
    polygon_name = Column(Text, nullable=False)

    def __init__(self, polygon_id, name):
        self.polygon_id = polygon_id
        self.polygon_name = name

    def __repr__(self):
        return "<LkPolygon(polygon_id=%r, polygon_name=%r)>" % (self.polygon_id, self.polygon_name)


# A table that uses the lookup tables via foreign keys.
class Widget(Base):
    __tablename__ = "widget__lookup_test"
    widget_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    colour_id = Column(Integer, ForeignKey("lk_colour__lookup_test.colour_id"), nullable=False)
    shape_id = Column(Integer, ForeignKey("lk_shape__lookup_test.shape_id"), nullable=False)
    colour = relationship(LkColour)
    shape = relationship(LkShape)


# These classes are fixtures as they have to be independent for each test case, as syncing to
# database modifies the class.
@pytest.fixture
def class_colour():
    class Colour(lookup.LookupTable):
        model = LkColour
        column_names = ("colour_id", "colour_name")

        ORANGE = LkColour(1, "orange")
        BLUE = LkColour(2, "blue")
        PURPLE = LkColour(3, "purple")

    return Colour


@pytest.fixture
def class_shape():
    class Shape(lookup.LookupTable):
        model = LkShape
        column_names = ("shape_id", "name", "corners")

        CIRCLE = LkShape(1, "circle", 0)
        SQUARE = LkShape(2, "square", 4)
        TRIANGLE = LkShape(3, "triangle", 3)

    return Shape


@pytest.fixture
def class_polygon():
    class Polygon(lookup.LookupTable):
        model = LkPolygon
        column_names = ("polygon_id", "polygon_name")

        TRIANGLE = LkPolygon(3, "triangle")
        SQUARE = LkPolygon(4, "square")
        PENTAGON = LkPolygon(5, "pentagon")

    return Polygon


def test_sync_to_database(test_db_session, class_colour):
    Colour = class_colour

    update_count = Colour.sync_to_database(test_db_session)
    assert update_count == 3
    test_db_session.commit()

    rows = (
        test_db_session.query(LkColour.colour_id, LkColour.colour_name)
        .order_by(LkColour.colour_id)
        .all()
    )
    assert rows == [(1, "orange"), (2, "blue"), (3, "purple")]


def test_sync_to_database_multi_column(test_db_session, class_shape):
    Shape = class_shape

    update_count = Shape.sync_to_database(test_db_session)
    assert update_count == 3
    test_db_session.commit()

    rows = (
        test_db_session.query(LkShape.shape_id, LkShape.name, LkShape.corners)
        .order_by(LkShape.shape_id)
        .all()
    )
    assert rows == [(1, "circle", 0), (2, "square", 4), (3, "triangle", 3)]


def test_sync_to_database_unmodified(test_db_session, class_shape):
    Shape = class_shape

    test_db_session.add_all(
        (LkShape(1, "circle", 0), LkShape(2, "square", 4), LkShape(3, "triangle", 3))
    )
    test_db_session.commit()

    # Write to database again.
    update_count = Shape.sync_to_database(test_db_session)
    assert update_count == 0
    test_db_session.commit()

    # Read back from database and verify.
    rows = (
        test_db_session.query(LkShape.shape_id, LkShape.name, LkShape.corners)
        .order_by(LkShape.shape_id)
        .all()
    )
    assert rows == [(1, "circle", 0), (2, "square", 4), (3, "triangle", 3)]


def test_sync_to_database_modified(test_db_session):
    class ShapeModified(lookup.LookupTable):
        model = LkShape
        column_names = ("shape_id", "name", "corners")

        CIRCLE = LkShape(1, "circle", 0)
        RECTANGLE = LkShape(2, "rectangle", 4)
        HEXAGON = LkShape(3, "hexagon", 6)
        OVAL = LkShape(4, "oval", 0)

    test_db_session.add_all(
        (LkShape(1, "circle", 0), LkShape(2, "square", 4), LkShape(3, "triangle", 3))
    )
    test_db_session.commit()

    # Modify and write to database again.
    update_count = ShapeModified.sync_to_database(test_db_session)
    assert update_count == 3
    test_db_session.commit()

    # Read back from database and verify.
    rows = (
        test_db_session.query(LkShape.shape_id, LkShape.name, LkShape.corners)
        .order_by(LkShape.shape_id)
        .all()
    )
    assert rows == [(1, "circle", 0), (2, "rectangle", 4), (3, "hexagon", 6), (4, "oval", 0)]


def test_attributes(test_db_session, class_colour, class_shape):
    Colour, Shape = class_colour, class_shape

    Colour.sync_to_database(test_db_session)
    Shape.sync_to_database(test_db_session)
    test_db_session.commit()

    assert Colour.ORANGE.colour_id == test_db_session.query(LkColour).get(1).colour_id
    assert Colour.PURPLE.colour_id == test_db_session.query(LkColour).get(3).colour_id
    assert Shape.TRIANGLE.shape_id == test_db_session.query(LkShape).get(3).shape_id
    assert Colour.ORANGE.colour_name == "orange"
    assert Colour.PURPLE.colour_name == "purple"
    assert Shape.TRIANGLE.name == "triangle"
    assert Shape.TRIANGLE.corners == 3


def test_get_instance_by_template(test_db_session, class_colour, class_shape):
    Colour, Shape = class_colour, class_shape

    Colour.sync_to_database(test_db_session)
    Shape.sync_to_database(test_db_session)
    test_db_session.commit()

    orange = Colour.get_instance(test_db_session, template=Colour.ORANGE)
    purple = Colour.get_instance(test_db_session, template=Colour.PURPLE)
    triangle = Shape.get_instance(test_db_session, template=Shape.TRIANGLE)
    assert orange.colour_id == 1
    assert purple.colour_id == 3
    assert triangle.shape_id == 3
    assert orange.colour_name == "orange"
    assert purple.colour_name == "purple"
    assert triangle.name == "triangle"
    assert triangle.corners == 3


def test_get_instance_by_description(test_db_session, class_colour):
    Colour = class_colour

    Colour.sync_to_database(test_db_session)
    test_db_session.commit()

    purple = Colour.get_instance(test_db_session, description="purple")
    assert purple.colour_id == 3
    assert purple.colour_name == "purple"


def test_get_instance_by_description_shared_by_lookups(test_db_session, class_shape, class_polygon):
    Shape, Polygon = class_shape, class_polygon

    Shape.sync_to_database(test_db_session)
    Polygon.sync_to_database(test_db_session)
    test_db_session.commit()

    square_shape = Shape.get_instance(test_db_session, description="square")
    assert square_shape.shape_id == 2
    assert square_shape.name == "square"
    assert type(square_shape) == LkShape

    square_polygon = Polygon.get_instance(test_db_session, description="square")
    assert square_polygon.polygon_id == 4
    assert square_polygon.polygon_name == "square"
    assert type(square_polygon) == LkPolygon


def test_get_instance_invalid_value(test_db_session, class_colour, class_shape):
    Colour, Shape = class_colour, class_shape

    Colour.sync_to_database(test_db_session)
    test_db_session.commit()

    green = LkColour(7, "green")

    with pytest.raises(TypeError):
        Colour.get_instance(test_db_session, template=Shape.CIRCLE)
    with pytest.raises(ValueError):
        Colour.get_instance(test_db_session, template=green)
    with pytest.raises(TypeError):
        Colour.get_instance(test_db_session)
    with pytest.raises(TypeError):
        Colour.get_instance(test_db_session, template=Shape.CIRCLE, description="square")


def test_get_id(test_db_session, class_colour):
    Colour = class_colour

    Colour.sync_to_database(test_db_session)
    test_db_session.commit()

    purple_id = Colour.get_id("purple")
    assert purple_id == 3


def test_lookup_modified_as_foreign_key(
    local_test_db_session, local_test_db_other_session, class_colour
):
    Colour = class_colour

    local_test_db_session.add_all(
        (LkShape(1, "circle", 0), LkShape(2, "square", 4), LkShape(3, "triangle", 3))
    )
    local_test_db_session.commit()

    class ShapeModified(lookup.LookupTable):
        model = LkShape
        column_names = ("shape_id", "name", "corners")

        CIRCLE = LkShape(1, "circle", 0)
        RECTANGLE = LkShape(2, "rectangle", 4)
        HEXAGON = LkShape(3, "hexagon", 6)
        OVAL = LkShape(4, "oval", 0)

    Colour.sync_to_database(local_test_db_other_session)
    ShapeModified.sync_to_database(local_test_db_other_session)
    local_test_db_other_session.commit()

    purple = Colour.get_instance(local_test_db_other_session, template=Colour.PURPLE)
    rect = ShapeModified.get_instance(local_test_db_other_session, template=ShapeModified.RECTANGLE)
    widget = Widget(name="Test widget 1", colour=purple, shape=rect)
    local_test_db_other_session.add(widget)
    local_test_db_other_session.commit()
    assert widget.colour == purple
    assert widget.shape == rect
    assert widget.colour_id == 3
    assert widget.shape_id == 2


def test_lookup_as_foreign_key(test_db_session, class_colour, class_shape):
    Colour, Shape = class_colour, class_shape

    Colour.sync_to_database(test_db_session)
    Shape.sync_to_database(test_db_session)
    test_db_session.commit()

    purple = Colour.get_instance(test_db_session, template=Colour.PURPLE)
    square = Shape.get_instance(test_db_session, template=Shape.SQUARE)
    widget = Widget(name="Test widget 1", colour=purple, shape=square)
    test_db_session.add(widget)
    test_db_session.commit()
    assert widget.colour == purple
    assert widget.shape == square
    assert widget.colour_id == 3
    assert widget.shape_id == 2


def test_lookup_as_foreign_key_using_template_instance(test_db_session, class_colour, class_shape):
    Colour, Shape = class_colour, class_shape

    Colour.sync_to_database(test_db_session)
    Shape.sync_to_database(test_db_session)
    test_db_session.commit()

    widget = Widget(name="Test widget 1", colour=Colour.PURPLE, shape=Shape.SQUARE)
    test_db_session.add(widget)

    # Expect to get an exception that looks like:
    #
    #   sqlalchemy.orm.exc.FlushError: New instance <LkColour at 0x7f27d6977760> with identity key
    #   (<class 'tests.db.test_lookup.LkColour'>, (3,), None)
    #   conflicts with persistent instance <LkColour at 0x7f27d6951dc0>
    with pytest.raises(sqlalchemy.orm.exc.FlushError):
        test_db_session.commit()


def test_lookup_as_foreign_key_by_id(test_db_session, class_colour, class_shape):
    Colour, Shape = class_colour, class_shape

    Colour.sync_to_database(test_db_session)
    Shape.sync_to_database(test_db_session)
    test_db_session.commit()

    widget = Widget(
        name="Test widget 1", colour_id=Colour.PURPLE.colour_id, shape_id=Shape.SQUARE.shape_id
    )
    test_db_session.add(widget)
    test_db_session.commit()

    purple = Colour.get_instance(test_db_session, template=Colour.PURPLE)
    square = Shape.get_instance(test_db_session, template=Shape.SQUARE)
    assert widget.colour == purple
    assert widget.shape == square
    assert widget.colour_id == 3
    assert widget.shape_id == 2


def test_lookup_modified_as_foreign_key_other_session(
    local_test_db_session, local_test_db_other_session, class_colour, class_shape
):
    Colour = class_colour
    Shape = class_shape

    local_test_db_session.add_all(
        (LkShape(1, "circle", 0), LkShape(2, "square", 4), LkShape(3, "triangle", 3))
    )
    local_test_db_session.commit()

    Colour.sync_to_database(local_test_db_session)
    Shape.sync_to_database(local_test_db_session)
    local_test_db_session.commit()

    purple = Colour.get_instance(local_test_db_other_session, Colour.PURPLE)
    square = Shape.get_instance(local_test_db_other_session, Shape.SQUARE)
    widget = Widget(name="Test widget 1", colour=purple, shape=square)
    local_test_db_other_session.add(widget)
    local_test_db_other_session.commit()
    assert widget.colour == purple
    assert widget.shape == square
    assert widget.colour_id == 3
    assert widget.shape_id == 2
