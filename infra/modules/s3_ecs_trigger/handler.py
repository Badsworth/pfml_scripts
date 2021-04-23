import boto3
import os

from botocore.config import Config

def handler(event, context):
    config = Config(
        retries = {
            'max_attempts': 3,
            'mode': 'standard'
        }
    )
        
    client = boto3.client('ecs', config=config)

    task_definition = os.environ["ECS_TASK_DEFINITION"]
    print(f"Attempting to run task {task_definition}")

    response = client.run_task(
        cluster=os.environ["ENVIRONMENT"],
        launchType='FARGATE',
        taskDefinition=task_definition,
        count=1,
        platformVersion='LATEST',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': os.environ['SUBNETS'].split(','),
                'securityGroups': os.environ['SECURITY_GROUPS'].split(','),
                'assignPublicIp': 'DISABLED'
            }
        })
        
    print("Finished invoking task.")
