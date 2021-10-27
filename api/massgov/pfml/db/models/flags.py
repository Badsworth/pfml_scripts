""" Grouping for tables related to feature flags """
# ORM models for feature flags
#
# A model's ORM representation should always match the database so we can
# properly read and write data. If you make a change, follow the instructions
# in the API README to generate an associated table migration.
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import object_session, relationship

import massgov.pfml.util.logging

from ..lookup import LookupTable
from .base import Base, TimestampMixin

logger = massgov.pfml.util.logging.get_logger(__name__)


class FeatureFlagValue(Base, TimestampMixin):
    __tablename__ = "feature_flag_value"
    feature_flag_value_id = Column(Integer, primary_key=True, autoincrement=True)
    feature_flag_id = Column(Integer, ForeignKey("lk_feature_flag.feature_flag_id"))
    enabled = Column(Boolean(), nullable=False)
    options = Column(JSONB, nullable=True)
    start = Column(TIMESTAMP(timezone=True), nullable=True)
    end = Column(TIMESTAMP(timezone=True), nullable=True)

    feature_flag = relationship("LkFeatureFlag")

    @property
    def name(self):
        return self.feature_flag.name


class LkFeatureFlag(Base):
    __tablename__ = "lk_feature_flag"
    feature_flag_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    default_enabled = Column(Boolean(), nullable=False)

    values = relationship("FeatureFlagValue")

    def logs(self, limit: Optional[int] = 10) -> Optional[list[FeatureFlagValue]]:
        # Use a query to include offset and limit.
        return (
            object_session(self)
            .query(FeatureFlagValue)
            .filter(FeatureFlagValue.feature_flag_id == self.feature_flag_id)
            .order_by(FeatureFlagValue.updated_at)
            .limit(limit)
            .offset(1)
            .all()
        )

    def _get_latest_feature_flag_value(self) -> Optional[FeatureFlagValue]:
        return (
            object_session(self)
            .query(FeatureFlagValue)
            .filter(FeatureFlagValue.feature_flag_id == self.feature_flag_id)
            .order_by(FeatureFlagValue.updated_at.desc())
            .first()
        )

    @property
    def enabled(self) -> bool:
        latest_value = self._get_latest_feature_flag_value()
        if latest_value is None:
            return self.default_enabled
        return latest_value.enabled

    def __init__(self, feature_flag_id, name, default_enabled):
        self.feature_flag_id = feature_flag_id
        self.name = name
        self.default_enabled = default_enabled


class FeatureFlag(LookupTable):
    model = LkFeatureFlag
    column_names = ("feature_flag_id", "name", "default_enabled")

    MAINTENANCE = LkFeatureFlag(1, "maintenance", False)


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    FeatureFlag.sync_to_database(db_session)
    db_session.commit()
