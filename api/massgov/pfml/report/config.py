from massgov.pfml.util.pydantic import PydanticBaseSettings


class ReportsS3Config(PydanticBaseSettings):
    s3_bucket: str
    environment: str
    sequential_employment_s3_path: str = "reports/sequential_employment/"
