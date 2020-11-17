from typing import Optional

import boto3
import boto3_extensions


def assume_session(
    role_arn: str,
    role_session_name: str,
    external_id: Optional[str] = None,
    region_name: Optional[str] = None,
) -> boto3.Session:
    """Get a boto3.Session for a role assumed via STS that automatically refreshes it's credentials"""
    session = boto3_extensions.get_role_session(
        role_arn=role_arn,
        external_id=external_id,
        role_session_name=role_session_name,
        region_name=region_name,
    )

    return session
