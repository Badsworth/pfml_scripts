from pydantic import BaseModel


class PydanticBaseModel(BaseModel):
    class Config:
        orm_mode = True
