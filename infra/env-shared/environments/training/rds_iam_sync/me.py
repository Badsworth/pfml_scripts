import boto3
import github
import os
import requests


def lambda_handler(event, context=None):
    github_token = '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'
    g = github.Github(github_token)
    g.get_user("wilfredokoro")
    org = g.get_organization("EOLWD")
    repo = g.get_repo("EOLWD/pfml").create_repository_dispatch(
        event_type="test_iam_refresh",
        client_payload={}
    )


def get_parameter()


client = boto3.client('ssm')
RDS_IAM_REFRESH = os.environ["RDS_IAM_REFRESH"]
response = client.get_parameter(
    Name='RDS_IAM_REFRESH',
    WithDecryption=True | False
)

headers = {'Authorization': "Bearer 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"}
requests.get('https://api.github.com/', headers=headers)
response = requests
print(response)


if __name__ == "__main__":
    lambda_handler({'environment': 'infra-test'})
