# just to get the namespace
from datetime import date
from typing import Optional

from pydantic import Field

from massgov.pfml.fineos.common import DOWNLOADABLE_DOC_TYPES

from . import spec as base  # noqa: F401


# Optional properties
class ManagedRequirementDetails(base.ManagedRequirementDetails):
    creationDate: Optional[date] = Field(  # type: ignore
        ..., description="ISO 8601 date format", example="1999-12-31"
    )
    dateSuppressed: Optional[date] = Field(  # type: ignore
        ..., description="ISO 8601 date format", example="1999-12-31"
    )


class GroupClientDocument(base.GroupClientDocument):
    def is_downloadable_by_leave_admin(self) -> bool:
        return self.name.lower() in DOWNLOADABLE_DOC_TYPES
