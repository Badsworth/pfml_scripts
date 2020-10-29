from typing import Optional

import boto3


def assume_session(
    role_arn: str,
    role_session_name: str,
    external_id: Optional[str] = None,
    duration_seconds: Optional[int] = 3600,
    region_name: Optional[str] = None,
) -> boto3.Session:
    aws_sts = boto3.client("sts", region_name=region_name)

    credentials = aws_sts.assume_role(
        RoleArn=role_arn,
        ExternalId=external_id,
        RoleSessionName=role_session_name,
        DurationSeconds=duration_seconds,
    )["Credentials"]

    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=region_name,
    )

    return session
