import boto3
import concurrent.futures
import datetime
import os
import traceback
import sys


class MetricAlarm:

    def __init__(self, metric_alarm):
        self.metric_alarm = metric_alarm

    def get(self, key, value=None):
        try:
            return self.metric_alarm[key]
        except KeyError:
            return value

    def alarm_name(self):
        return self.get('AlarmName')

    @staticmethod
    def stringify(iterable):
        return ', '.join(iterable)

    def get_alarm_actions(self):
        return self.stringify(self.get('AlarmActions'))

    def get_ok_actions(self):
        return self.stringify(self.get('OKActions'))

    def get_insufficient_data_actions(self):
        return self.stringify(self.get('InsufficientDataActions'))

    def to_dict(self):
        return {
            'ResourceName': self.alarm_name(),
            'DateAudited': str(datetime.datetime.now()),
            'AlarmArn': self.get('AlarmArn'),
            'AlarmDescription': self.get('AlarmDescription'),
            'LastModified': self.get('AlarmConfigurationUpdatedTimestamp'),
            'ActionsEnabled': self.get('ActionsEnabled'),
            'AlarmActions': self.stringify(self.get('AlarmActions')),
            'OKActions': self.stringify(self.get('OKActions')),
            'InsufficientDataActions': self.stringify(self.get('InsufficientDataActions')),
            'CurrentAlarmState': self.get('StateValue'),
            'CurrentAlarmReason': self.get('StateReason'),
            'MetricName': self.get('MetricName'),
            'Namespace': self.get('Namespace'),
            'Statistic': self.get('Statistic'),
            'PercentileStatistic': self.get('ExtendedStatistic'),
            'Period': self.get('Period'),
            'EvaluationPeriods': self.get('EvaluationPeriods'),
            'Unit': self.get('Unit'),
            'DatapointsToAlarm': self.get('DatapointsToAlarm'),
            'Threshold': self.get('Threshold'),
            'ComparisonOperator': self.get('ComparisonOperator'),
        }


def region():
    return os.environ.get('REGION')

def list_alarms():
    return [
        alarm for page in PAGINATED_LIST_OF_ALARMS.paginate()
        for alarm in page['MetricAlarms']
    ]

def write_to_dynamodb(data):
    return TABLE.put_item(Item=data.to_dict())

def display_results(executions):
    for execution in concurrent.futures.as_completed(executions):
        try:
            print(f'{executions[execution]} succeeded: {execution.result()}')
        except Exception:
            print(f'{executions[execution]} failed: ')
            traceback.print_exception(*sys.exc_info())

def handler(event, context):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        display_results({
            executor.submit(
                write_to_dynamodb,
                cloudwatch_alarm,
            ): f'auditing {cloudwatch_alarm["FunctionName"]}'
            for cloudwatch_alarm in list_alarms()
        })

CLOUDWATCH = boto3.client("cloudwatch")
PAGINATED_LIST_OF_ALARMS = CLOUDWATCH.get_paginator("describe_alarms")
TABLE = boto3.resource(
    'dynamodb',
    endpoint_url=f'https://dynamodb.{region()}.amazonaws.com'
).Table(
    os.environ.get('INVENTORY_TABLE_NAME')
)