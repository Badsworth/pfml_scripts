from pydantic import UUID4

from massgov.pfml.util.pydantic import PydanticBaseModel


class RoleRequest(PydanticBaseModel):
    role_description: str


class RoleUserDeleteRequest(PydanticBaseModel):
    role: RoleRequest
    user_id: UUID4
