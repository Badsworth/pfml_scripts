from bouncer.constants import EDIT, READ  # noqa: F401 F403
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

import massgov.pfml.util.logging

from ..lookup import LookupTable
from .base import Base, TimestampMixin

logger = massgov.pfml.util.logging.get_logger(__name__)


class LkAzurePermission(Base):
    __tablename__ = "lk_azure_permission"
    azure_permission_id = Column(Integer, primary_key=True, autoincrement=True)
    azure_permission_description = Column(Text, nullable=False)
    azure_permission_resource = Column(Text, nullable=False)
    azure_permission_action = Column(Text, nullable=False)

    def __init__(
        self,
        azure_permission_id,
        azure_permission_description,
        azure_permission_resource,
        azure_permission_action,
    ):
        self.azure_permission_id = azure_permission_id
        self.azure_permission_description = azure_permission_description
        self.azure_permission_resource = azure_permission_resource
        self.azure_permission_action = azure_permission_action


class AzureGroupPermission(Base, TimestampMixin):
    __tablename__ = "link_azure_group_permission"
    azure_permission_id = Column(
        Integer, ForeignKey("lk_azure_permission.azure_permission_id"), primary_key=True
    )
    azure_group_id = Column(Integer, ForeignKey("lk_azure_group.azure_group_id"), primary_key=True)


class LkAzureGroup(Base):
    __tablename__ = "lk_azure_group"
    azure_group_id = Column(Integer, primary_key=True, autoincrement=True)
    azure_group_name = Column(Text, nullable=False)
    azure_group_guid = Column(Text, nullable=False)
    azure_group_parent_id = Column(
        Integer, ForeignKey("lk_azure_group.azure_group_id"), nullable=True
    )
    permissions = relationship(AzureGroupPermission, uselist=True)

    def __init__(self, azure_group_id, azure_group_name, azure_group_guid, azure_group_parent_id):
        self.azure_group_id = azure_group_id
        self.azure_group_name = azure_group_name
        self.azure_group_guid = azure_group_guid
        self.azure_group_parent_id = azure_group_parent_id


class UserAzurePermissionLog(Base, TimestampMixin):
    __tablename__ = "user_azure_permission_log"
    user_azure_permission_log_id = Column(Integer, primary_key=True, autoincrement=True)
    email_address = Column(Text, nullable=False)
    sub_id = Column(Text, nullable=False)
    family_name = Column(Text, nullable=False)
    given_name = Column(Text, nullable=False)
    azure_permission_id = Column(Integer, ForeignKey("lk_azure_permission.azure_permission_id"))
    azure_group_id = Column(Integer, ForeignKey("lk_azure_group.azure_group_id"))
    action = Column(Text, nullable=False)


class AzureGroup(LookupTable):
    model = LkAzureGroup
    column_names = (
        "azure_group_id",
        "azure_group_name",
        "azure_group_guid",
        "azure_group_parent_id",
    )

    NON_PROD = LkAzureGroup(
        1, "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD", "67f909a7-049b-4844-98eb-beec1bd35fc0", None
    )
    NON_PROD_ADMIN = LkAzureGroup(
        2,
        "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD_ADMIN",
        "1af1bd6d-2a32-405d-9d90-7b126be8b9fa",
        NON_PROD.azure_group_id,
    )
    NON_PROD_DEV = LkAzureGroup(
        3,
        "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD_DEV",
        "d268edaa-4c0e-48ff-82c0-012e224ddda3",
        NON_PROD.azure_group_id,
    )
    NON_PROD_CONTACT_CENTER = LkAzureGroup(
        4,
        "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD_CONTACT_CENTER",
        "13d579da-bb84-4c5f-a382-93584fc9e91f",
        NON_PROD.azure_group_id,
    )
    NON_PROD_SERVICE_DESK = LkAzureGroup(
        5,
        "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD_SERVICE_DESK",
        "e483a1df-5ce4-4e94-a9bc-48dacf4a14f4",
        NON_PROD.azure_group_id,
    )
    NON_PROD_DFML_OPS = LkAzureGroup(
        6,
        "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD_DFML_OPS",
        "be96c3c2-5d2b-4845-9ed5-bb0aa109009e",
        NON_PROD.azure_group_id,
    )
    PROD = LkAzureGroup(
        7, "TSS-SG-PFML_ADMIN_PORTAL_PROD", "ccda65ae-07e1-4db8-b9ad-891e882698f3", None
    )
    PROD_ADMIN = LkAzureGroup(
        8,
        "TSS-SG-PFML_ADMIN_PORTAL_PROD_ADMIN",
        "68800ca3-9f10-48e9-9e41-b62de7a48dfb",
        PROD.azure_group_id,
    )
    PROD_DEV = LkAzureGroup(
        9, "TSS-SG-PFML_ADMIN_PORTAL_PROD_DEV (reserved)", "9", PROD.azure_group_id
    )
    PROD_CONTACT_CENTER = LkAzureGroup(
        10, "TSS-SG-PFML_ADMIN_PORTAL_PROD_CONTACT_CENTER (reserved)", "10", PROD.azure_group_id
    )
    PROD_SERVICE_DESK = LkAzureGroup(
        11, "TSS-SG-PFML_ADMIN_PORTAL_PROD_SERVICE_DESK (reserved)", "11", PROD.azure_group_id
    )
    PROD_DFML_OPS = LkAzureGroup(
        12, "TSS-SG-PFML_ADMIN_PORTAL_PROD_DFML_OPS (reserved)", "12", PROD.azure_group_id
    )


class AzurePermission(LookupTable):
    model = LkAzurePermission
    column_names = (
        "azure_permission_id",
        "azure_permission_description",
        "azure_permission_resource",
        "azure_permission_action",
    )

    USER_READ = LkAzurePermission(1, "USER_READ", "USER", READ)
    USER_EDIT = LkAzurePermission(2, "USER_EDIT", "USER", EDIT)
    LOG_READ = LkAzurePermission(3, "LOG_READ", "LOG", READ)
    DASHBOARD_READ = LkAzurePermission(4, "DASHBOARD_READ", "DASHBOARD", READ)
    SETTINGS_READ = LkAzurePermission(5, "SETTINGS_READ", "SETTINGS", READ)
    SETTINGS_EDIT = LkAzurePermission(6, "SETTINGS_EDIT", "SETTINGS", EDIT)
    MAINTENANCE_READ = LkAzurePermission(7, "MAINTENANCE_READ", "MAINTENANCE", READ)
    MAINTENANCE_EDIT = LkAzurePermission(8, "MAINTENANCE_EDIT", "MAINTENANCE", EDIT)
    FEATURES_READ = LkAzurePermission(9, "FEATURES_READ", "FEATURES", READ)
    FEATURES_EDIT = LkAzurePermission(10, "FEATURES_EDIT", "FEATURES", EDIT)


def sync_azure_permissions(db_session):
    """Insert every permission for non_prod and prod admin groups."""
    group_ids = [AzureGroup.NON_PROD_ADMIN.azure_group_id, AzureGroup.PROD_ADMIN.azure_group_id]
    permissions = AzurePermission.get_all()
    for group_id in group_ids:
        group_permission_ids = [
            p_id[0]
            for p_id in db_session.query(AzureGroupPermission.azure_permission_id).filter(
                AzureGroupPermission.azure_group_id == group_id
            )
        ]
        for permission in permissions:
            if permission.azure_permission_id not in group_permission_ids:
                logger.info(
                    "Adding AzureGroupPermission record",
                    extra={
                        "azure_permission_id": permission.azure_permission_id,
                        "azure_group_id": group_id,
                    },
                )
                db_session.add(
                    AzureGroupPermission(
                        azure_group_id=group_id, azure_permission_id=permission.azure_permission_id
                    )
                )
    db_session.commit()


def sync_lookup_tables(db_session):
    AzureGroup.sync_to_database(db_session)
    AzurePermission.sync_to_database(db_session)
