#!/usr/bin/env python3

import inspect
import secrets
import string
from contextlib import contextmanager
from typing import Generator, Optional

import boto3
import click

from massgov.pfml.util.aws_ssm import get_secret, put_secret


@click.command()
@click.option("-d", "--dry-run", is_flag=True, default=False)
@click.option(
    "-p", "--password", help="Password to use. If not provided, a random one will be generated."
)
@click.argument("data_mart_env", type=click.Choice(["UAT", "PROD"], case_sensitive=False))
def main(data_mart_env: str, dry_run: bool, password: Optional[str]) -> None:
    """Set a new password for all API environments that utilize the given Data Mart environment (UAT or PROD).

    Note, this only sets up the configuration for the new password in the API
    environment(s), in order for the new password to take effect in Data Mart
    the rotate password task must be run.
    """
    ssm = boto3.client("ssm")

    click.echo(f"Generating and configuring new password for Data Mart env {data_mart_env}\n")

    if data_mart_env == "UAT":
        api_envs = ["performance"]
    else:
        api_envs = ["prod"]

    current_data_mart_password = get_secret(ssm, current_data_mart_ssm_key_for_env(api_envs[0]))

    new_data_mart_password = password or generate_password(20)

    if current_data_mart_password == new_data_mart_password:
        click.secho("Current and new password are the same", fg="yellow")
        click.echo("")

    for api_env in api_envs:
        click.echo(f"Configuring {api_env}")

        old_data_mart_ssm_key = old_data_mart_ssm_key_for_env(api_env)
        current_data_mart_ssm_key = current_data_mart_ssm_key_for_env(api_env)

        if dry_run:
            click.echo(f"  Would set {old_data_mart_ssm_key} to {current_data_mart_password}")
            click.echo(f"  Would set {current_data_mart_ssm_key} to {new_data_mart_password}")
        else:
            with print_status_line(f"  Saving current password to {old_data_mart_ssm_key}"):
                put_secret(ssm, old_data_mart_ssm_key, current_data_mart_password)

            with print_status_line(f"  Saving new password to {current_data_mart_ssm_key}"):
                put_secret(ssm, current_data_mart_ssm_key, new_data_mart_password)

    click.echo("")
    if dry_run:
        click.echo(
            inspect.cleandoc(
                f"""
                New password would have been configured in API envs {api_envs},
                but would not have been rotated in Data Mart.  Running the
                rotate password task is required to actually make the change in
                Data Mart.
                """
            )
        )
    else:
        click.echo(
            inspect.cleandoc(
                f"""
                New password has been configured in API envs {api_envs}, but has
                not been rotated in Data Mart. Run the rotate password task to
                actually make the change in Data Mart.
                """
            )
        )


def generate_password(num_chars: int) -> str:
    alphabet = string.digits + string.ascii_letters + string.punctuation.replace("'", "")

    while True:
        password = "".join(secrets.choice(alphabet) for i in range(num_chars))
        if (
            any(c.isdigit() for c in password)
            and any(c.isalpha() for c in password)
            and any(not c.isalnum() for c in password)
        ):
            break

    return password


def current_data_mart_ssm_key_for_env(api_env: str) -> str:
    return f"/service/pfml-api/{api_env}/ctr-data-mart-password"


def old_data_mart_ssm_key_for_env(api_env: str) -> str:
    return current_data_mart_ssm_key_for_env(api_env) + "-old"


@contextmanager
def print_status_line(start_msg: str) -> Generator[None, None, None]:
    click.echo(start_msg, nl=False)
    try:
        yield
        click.secho(" ✔", fg="green")
    except Exception:
        click.secho(" ❌", fg="red")
        raise


if __name__ == "__main__":
    main()
