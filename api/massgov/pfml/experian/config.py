from pydantic import Field

import massgov.pfml.util.pydantic


class ExperianConfig(massgov.pfml.util.pydantic.PydanticBaseSettings):
    auth_token: str = Field(..., min_length=1)
    base_url: str = Field("https://api.experianaperture.io", min_length=1)

    class Config:
        env_prefix = "EXPERIAN_"
