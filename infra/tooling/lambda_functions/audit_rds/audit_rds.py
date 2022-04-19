import boto3
import os
import datetime
import concurrent.futures
import traceback
import sys


class Database(object):

    def __init__(self, database):
        self.database = database

    def get(self, key, default=None):
        return self.database.get(key, default)

    def database_name(self):
        return self.get('DatabaseName')

    def get_availability_zones(self):
        return ", ".join(self.get('AvailabilityZones'))

    def get_security_group_ids(self):
        return ', '.join(security_group['VpcSecurityGroupId'] for security_group in self.get('VpcSecurityGroups'))

    def get_iam_roles(self):
        return ', '.join(role['RoleArn'] for role in self.get('AssociatedRoles'))

    def get_tags(self):
        try:
            return {
                tag['Key']: tag['Value'] for tag in self.get('TagList')
            }
        except (AttributeError, TypeError):
            return {}

    def to_dict(self):
        return {
            'ResourceName': self.database_name(),
            'DateAudited': str(datetime.datetime.now()),
            'ClusterIdentifier': self.get('DBClusterIdentifier'),
            'AvailabilityZones': self.get_availability_zones(),
            'Endpoint': self.get('Endpoint'),
            'MultiAZ': self.get('MultiAZ'),
            'Engine': self.get('Engine'),
            'LastRestorableTime': self.get('LatestRestorableTime'),
            'PreferredBackupWindow': self.get('PreferredBackupWindow'),
            'EncryptedStorage': self.get('StorageEncrypted'),
            'KmsKeyId': self.get('KmsKeyId'),
            'AssociatedIamRoles': self.get_iam_roles(),
            'IAMDatabaseAuthenticationEnabled': self.get('IAMDatabaseAuthenticationEnabled'),
            'DeletionProtection': self.get('DeletionProtection'),
            'DbInstanceClass': self.get('DBClusterInstanceClass'),
            'PerformanceInsightsEnabled': self.get('PerformanceInsightsEnabled'),
            'AutoMinorVersionUpgrade': self.get('AutoMinorVersionUpgrade'),
            'StorageType': self.get('StorageType'),
            'SecurityGroupIds': self.get_security_group_ids(),
            **self.get_tags(),
        }

def region():
    return os.environ.get('REGION')

def get_list_of_databases():
    return (
        database for database
        in RDS.describe_db_clusters()['DBClusters']
    )

def write_to_dynamodb(data):
    return TABLE.put_item(Item=Database(data).to_dict())

def display_results(executions):
    for execution in concurrent.futures.as_completed(executions):
        try:
            print(f'{executions[execution]} succeeded: {execution.result()}')
        except Exception:
            print(f'{executions[execution]} failed: {execution.exception()}')
            traceback.print_exception(*sys.exc_info())

def handler(event, context):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        display_results({
            executor.submit(
                write_to_dynamodb,
                database,
            ): f'auditing {database["DatabaseName"]}'
            for database in get_list_of_databases()
        })

RDS = boto3.session.Session(region_name=region()).client('rds')
TABLE = boto3.resource(
    'dynamodb',
    endpoint_url=f'https://dynamodb.{region()}.amazonaws.com'
).Table(
    os.environ.get('INVENTORY_TABLE_NAME')
)
