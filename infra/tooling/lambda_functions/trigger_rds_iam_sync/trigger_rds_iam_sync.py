import boto3
import github

SSM = boto3.client('ssm', region_name="us-east-1")

def get_github_token():
    return SSM.get_parameter(
        Name='/service/pfml-api/github/trigger-rds-iam-sync-token',
        WithDecryption=True
    )['Parameter']['Value']

def handler(event, context=None):
    github_client = github.Github(
        login_or_token=get_github_token()
    )
    eolwd = github_client.get_repo('EOLWD/pfml')
    result = eolwd.create_repository_dispatch(
        event_type='trigger_rds_iam_sync',
    )

    if result:
        print('Triggering API RDS IAM Sync for Training Database')

if __name__ == "__main__":
    handler(None)

# to do
# connect event bridge to lambda
# setup pattern for event bridge to trigger lambda
# RDS - EventBridge - Lambda - GitHub Action
