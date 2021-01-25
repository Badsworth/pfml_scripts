# API Monitoring

We use New Relic (for performance monitoring, synthetics, and general queries)
and AWS CloudWatch (for infrastructure-level concerns) to monitor the PFML API.

We get CloudWatch metrics for free just by deploying the API on AWS Fargate,
but the New Relic metrics are sourced from a Python agent that is initialized during server startup.


## AWS CloudWatch

- [Alarms index](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:)
- [SNS topics index](https://console.aws.amazon.com/sns/v3/home?region=us-east-1#)
- [Available CloudWatch metrics](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~())

The API's AWS monitoring is defined in Terraform under `infra/api/template/alarms.tf`.

When an alarm triggers, it will push an event to one or more SNS topics, also defined in `alarms.tf`.
If configured to do so, SNS events can also be generated when an alarm stops alarming and returns to a normal state.

To subscribe to AWS alerts, you can do one of two things.

- You can use the AWS console to create a temporary subscription to one or more SNS topics,
  but these subscriptions will only last until someone re-applies the canonical Terraform config.
- You can define a new `aws_sns_topic_subscription` object in `alarms.tf`.


## New Relic

- [Main index](https://rpm.newrelic.com/accounts/1606654/applications)
    - Note: Includes applications not owned by Nava. Filter by `pfml` to see only the PFML API.

Most configuration is sourced from `api/newrelic.ini` except for the license key,
which is sourced from AWS SSM and provided at runtime as an environment variable.

At this time, New Relic API monitoring is limited only to data collection. Alarms have not yet been configured here.
