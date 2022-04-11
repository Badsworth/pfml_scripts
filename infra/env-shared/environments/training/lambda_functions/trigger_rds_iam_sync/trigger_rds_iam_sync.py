import boto3
import github

SSM = boto3.client('ssm', region_name="us-east-1")

def get_github_token():
    return SSM.get_parameter(
        Name='/service/pfml-api/github/trigger-rds-iam-sync-token',
        WithDecryption=True
    )['Parameter']['Value']

def lambda_handler(event, context=None):
    github_client = github.Github(
        login_or_token=get_github_token()
    )
    # eolwd = github_client.get_repo('EOLWD/pfml')
    eolwd = github_client.get_repo('EOLWD/pfml/tree/wilfredokoro/INFRA-1363-add-repository-dispatch-to-rds-iam-sync-github-action')
    result = eolwd.create_repository_dispatch(
        event_type='trigger_rds_iam_sync',
    )

    if result:
        print('Triggering API RDS IAM Sync for Training Database')

if __name__ == "__main__":
    lambda_handler(None)

# to do
# Add repo dispatch to rds_iam_sync github action
# - My branch  
# - Main
# Test repo dispatch to rds_iam_sync github action 
# - My branch  
# - Main

