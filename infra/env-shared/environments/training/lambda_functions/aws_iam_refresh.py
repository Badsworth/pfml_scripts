import boto3
import github

SSM = boto3.client('ssm', region_name="us-east-1")

def get_github_token():
    return SSM.get_parameter(
        Name='/service/pfml-api/rds-iam-sync',
        WithDecryption=True
    )['Parameter']['Value']

def trigger_rds_iam_sync():
    github_client = github.Github(
        login_or_token=get_github_token()
    )
    eolwd = github_client.get_repo('EOLWD/pfml')
    result = eolwd.create_repository_dispatch(
        event_type='rds_iam_sync',

    )
    print(result)

def lambda_handler(event, context=None):
    trigger_rds_iam_sync()

if __name__ == "__main__":
    lambda_handler(None)
