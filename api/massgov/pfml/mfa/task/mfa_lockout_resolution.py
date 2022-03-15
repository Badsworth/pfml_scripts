import argparse
import sys
from typing import List

from massgov.pfml.mfa.mfa_lockout_resolver import MfaLockoutResolver
from massgov.pfml.util.bg import background_task


def _parse_script_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Disables MFA for users who have become locked out of their accounts due to an MFA issue"
    )

    parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="(Required) The email associated with the user's PFML account",
    )

    parser.add_argument(
        "--psd_number",
        type=str,
        required=True,
        help="(Required) The PSD ticket number of the request to disable MFA (eg 'PSD-9876'). \
            If none provided, put 'None Provided'",
    )

    parser.add_argument(
        "--reason",
        type=str,
        required=True,
        help="(Required) The user's reason for disabling MFA (eg 'Lost their phone'). \
            If none provided, put 'None Provided'",
    )

    parser.add_argument(
        "--employee",
        type=str,
        required=True,
        help="(Required) The email address of the contact center agent who filed the request. \
            If none provided, put 'None Provided'",
    )

    parser.add_argument(
        "--verification_method",
        type=str,
        required=True,
        help="(Required) The method used to verify the user's identity ('With Claim' or 'Without Claim'). \
            If none provided, put 'None Provided'",
    )

    parser.add_argument(
        "--dry_run",
        type=str,
        default="True",
        help="(Optional) Defaults to 'True'. \
            Set this to 'False' to allow the script to commit changes to Amazon Cognito and the PFML db",
    )

    return parser.parse_args(args)


@background_task("mfa-lockout-resolution")
def main() -> None:
    args = sys.argv[1:]
    parsed_args = _parse_script_args(args)

    user_email = parsed_args.email
    psd_number = parsed_args.psd_number.upper()
    reason_for_disabling = parsed_args.reason
    agent_email = parsed_args.employee
    verification_method = parsed_args.verification_method

    # dry_run defaults to true unless "false" is explicitly passed in
    dry_run = not (parsed_args.dry_run.lower() == "false")

    lockout_resolver = MfaLockoutResolver(
        user_email, psd_number, reason_for_disabling, agent_email, verification_method, dry_run
    )
    lockout_resolver.run()
