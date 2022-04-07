#from email import header
#import boto3



import os

import requests

def lambda_handler(event, context=None):

    client = boto3.client('ssm')
    RDS_IAM_REFRESH = os.environ["RDS_IAM_REFRESH"]


#response = client.get_parameter(
 #   Name='RDS_IAM_REFRESH',
 #   WithDecryption=True|False
 #   )
headers = {'Authorization': "Bearer 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"}
requests.get('https://api.github.com/',headers=headers)
response = requests
print(response)




#curl -X GET -u tcruzsmx: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" -H "Accept: application/vnd.github.v3+json" https://api.github.com/EOLWD/pfml/security/dependabot/62

#header
