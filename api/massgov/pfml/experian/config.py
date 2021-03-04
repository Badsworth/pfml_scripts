from pydantic import BaseSettings, Field


class ExperianConfig(BaseSettings):
    auth_token: str = Field(..., min_length=1)
    base_url: str = Field("https://api.experianaperture.io", min_length=1)

    class Config:
        env_prefix = "EXPERIAN_"
