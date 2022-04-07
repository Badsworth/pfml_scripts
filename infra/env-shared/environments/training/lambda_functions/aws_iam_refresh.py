import boto3
import github
import os
import requests

# SSM = boto3.client('ssm', region_name="us-east-1")
# RDS_IAM_REFRESH = os.environ["RDS_IAM_REFRESH"]

# headers = {'Authorization': "Bearer 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"}
# requests.get('https://api.github.com/', headers=headers)
# response = requests
# print(response)

def get_parameter():
    return SSM.get_parameter(
        Name='RDS_IAM_REFRESH',
        WithDecryption=True | False
    )

def github_token():
    return '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'

def trigger_github_action(environment='training'):
    github_client = github.Github(login_or_token=github_token())
    eolwd = github_client.get_repo('EOLWD/pfml')
    result = eolwd.create_repository_dispatch(
        event_type='rds_iam_refresh',
        # client_payload={
        #     'environment': environment
        # },
    )
    print(result)

def lambda_handler(event, context=None):
    trigger_github_action()


if __name__ == "__main__":
    lambda_handler({'environment': 'infra-test'})