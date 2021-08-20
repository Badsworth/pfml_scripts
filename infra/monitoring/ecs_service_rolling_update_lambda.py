import boto3
import botocore


cluster_names = lambda: [arn.split("/")[1] for arn in boto3.client('ecs').list_clusters()['clusterArns']]


def rolling_refresh(cluster_name):
    ''' Performs rolling refresh for the pfml-api service in given cluster '''

    try:
        boto3.client('ecs').update_service(
            cluster=cluster_name,
            service=f"pfml-api-{cluster_name}",
            forceNewDeployment=True
        )
    except botocore.exceptions.ClientError as error:
        return cluster_name, str(error)

    return cluster_name, "update_service call success"
    

def lambda_handler(event, context=None):
    ''' entrypoint for lambda '''

    return dict(map(rolling_refresh, cluster_names()))
