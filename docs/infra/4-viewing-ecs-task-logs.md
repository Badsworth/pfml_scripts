# Viewing ECS Task logs

The logs for all background ECS tasks are sent to Cloudwatch Logs and New Relic. There are two distinct methods that people use:

## Streaming logs to your terminal

Lots of folks use [saw](https://github.com/TylerBrock/saw) and pipe it through a developer utility for pretty-printing logs:

```sh
saw watch --raw service/pfml-api-test/ecs-tasks | python3 api/massgov/pfml/util/logging/decodelog.py
```

You can also use the AWS CLI v2, which has built in support for tailing Cloudwatch logs:

```sh
aws logs tail service/pfml-api-test/ecs-tasks --follow
```

Common log groups that may be useful:

| Log Group Pattern                     | Description                            |
|---------------------------------------|----------------------------------------|
| service/pfml-api-ENV                  | Application logs from the PFML API ECS tasks|
| service/pfml-api-ENV/ecs-tasks        | Application logs from all background job ECS tasks|
| service/pfml-api-ENV/ecs-tasks/events | State change events from all ECS tasks |

## Searching logs in New Relic

Alternatively, you can use the New Relic Logs UI to search and filter for logs. See [New Relic's documentation](https://docs.newrelic.com/docs/logs/log-management/ui-data/query-syntax-logs/) for more information on the query syntax for log data. There is a saved view for [ECS task logs in TEST](https://one.newrelic.com/launcher/logger.log-launcher?platform[accountId]=2837112&platform[$isFallbackTimeRange]=true&platform[timeRange][duration]=1800000&launcher=eyJxdWVyeSI6ImF3cy5sb2dHcm91cDpcInNlcnZpY2UvcGZtbC1hcGktdGVzdC9lY3MtdGFza3NcIiAtbGV2ZWxuYW1lOkFVRElUIiwiZXZlbnRUeXBlcyI6WyJMb2ciXSwiYWN0aXZlVmlldyI6IlZpZXcgQWxsIExvZ3MiLCJpc0VudGl0bGVkIjp0cnVlLCJhdHRycyI6WyJhd3MubG9nU3RyZWFtIiwibGV2ZWxuYW1lIiwidGltZXN0YW1wIiwibmFtZSIsImZ1bmNOYW1lIiwiYXdzLmxvZ0dyb3VwIiwibWVzc2FnZSJdLCJiZWdpbiI6bnVsbCwiZW5kIjpudWxsfQ==&pane=eyJuZXJkbGV0SWQiOiJsb2dnZXIuaG9tZSIsIiRzZGtWZXJzaW9uIjozfQ==&state=40e1ffea-4230-c73f-5e18-4f1427542446), and you can further filter based on the task name:

```
aws.logStream:*my-new-task-name*
```

##### Viewing start failure reasons

If your task does not start successfully, there will be no logs. Instead, there will be a Slack notification in #mass-pfml-pd-warnings with a description of your error.

These failure messages will also be available for up to an hour in [the ECS AWS console](https://console.aws.amazon.com/ecs/home?region=us-east-1#), and more indefinitely in the state change logs stored under `service/pfml-api-ENV/ecs-tasks/events`. Use one of the methods above to view logs in this log group.
