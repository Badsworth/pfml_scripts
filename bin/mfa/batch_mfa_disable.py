import argparse
import json
import os
import sys

def entrypoint():
    """
    Helper script to run batch disable claimant mfa
    """
    main(sys.argv[1:])

def main(raw_args: list) -> None:
    client_args = parse_args(raw_args)
    results = disable_mfa(client_args)

# Parse arguments from the user
def parse_args(raw_args: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--environment", type=str, help="Environment to run mfa_diasble against")
    parser.add_argument("-d", "--dry_run", type=str, help="Dry run true or false, true will not disable MFA and only log")
    parser.add_argument("-u", "--user", type=str, help="User running the script, example jay.reed")
    client_args = parser.parse_args()
    return client_args

# pull json file into python dictionary and disable mfa for all claimants in file
def disable_mfa(client_args):
    with open('claimants.json') as data:
        claimants = json.load(data)
    
    success = True

    for claimant in claimants:
        try:
            os.system(f"../run-ecs-task/run-task.sh {client_args.environment} mfa-lockout-resolution {client_args.user} mfa-lockout-resolution --email={claimant['email']} --psd_number={claimant['psd_number']} --reason='{claimant['reason']}' --employee={claimant['employee']} --verification_method='{claimant['verification_method']}' --dry_run={client_args.dry_run}")
            print(f"ecs task scheduled to disable mfa for claimant in {claimant['psd_number']}")
        except Exception as e:
            print(e)
            success = False
    return success


if __name__ == "__main__":
    entrypoint()

