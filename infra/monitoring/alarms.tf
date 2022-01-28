# Terraform configuration for any alarm that's stored in New Relic.

locals {
  environments = ["test", "stage", "prod", "performance", "training", "uat", "breakfix", "cps-preview", "long", "trn2"]
}

module "alarms_api" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_api"

  environment_name                 = each.key
  low_priority_nr_integration_key  = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  high_priority_nr_integration_key = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
  warning_alert_sns_topic_arn      = aws_sns_topic.api-low-priority-alerts-topic.arn
  critical_alert_sns_topic_arn     = each.key == "prod" ? aws_sns_topic.api-high-priority-alerts-topic.arn : aws_sns_topic.api-low-priority-alerts-topic.arn
  enable_alarm_api_cpu             = each.key != "test"
  enable_alarm_api_ram             = each.key != "test"
}

module "alarms_portal" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_portal"

  environment_name                        = each.key
  low_priority_nr_portal_integration_key  = pagerduty_service_integration.newrelic_low_priority_portal_notification.integration_key
  high_priority_nr_portal_integration_key = pagerduty_service_integration.newrelic_high_priority_portal_notification.integration_key
}

module "email_bounce" {
  source = "../modules/email_bounce"

  low_priority_nr_integration_key  = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  high_priority_nr_integration_key = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
}

module "sns_alarms" {
  source                           = "../modules/terraform_sns_alarms"
  sns_monthly_spend_limit          = module.constants.aws_sns_sms_monthly_spend_limit
  low_priority_nr_integration_key  = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  high_priority_nr_integration_key = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
}

module "sns_vpc_changes" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "vpc_changes"
  alarm_description = "VPC Changes Occured"
  metric_name       = "VpcChanges"
  namespace         = "LogMetrics"
  pattern           = "{ ($.eventName = CreateVpc) || ($.eventName = DeleteVpc) || ($.eventName = ModifyVpcAttribute) || ($.eventName = AcceptVpcPeeringConnection) || ($.eventName = CreateVpcPeeringConnection) || ($.eventName = DeleteVpcPeeringConnection) || ($.eventName = RejectVpcPeeringConnection) || ($.eventName = AttachClassicLinkVpc) || ($.eventName = DetachClassicLinkVpc) || ($.eventName = DisableVpcClassicLink) || ($.eventName = EnableVpcClassicLink) }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_route_tables_changes" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "route_tables_changes"
  alarm_description = "Route Table Changes Occured"
  metric_name       = "RouteTableChanges"
  namespace         = "LogMetrics"
  pattern           = "{($.eventName = CreateRoute) || ($.eventName = CreateRouteTable) || ($.eventName = ReplaceRoute) || ($.eventName = ReplaceRouteTableAssociation) || ($.eventName = DeleteRouteTable) || ($.eventName = DeleteRoute) || ($.eventName = DisassociateRouteTable) }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_network_gateway_changes" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "network_gateway_changes"
  alarm_description = "Network Gateway Changes Occured"
  metric_name       = "NetworkGatewayChanges"
  namespace         = "LogMetrics"
  pattern           = "{($.eventName = CreateCustomerGateway) || ($.eventName = DeleteCustomerGateway) || ($.eventName = AttachInternetGateway) || ($.eventName = CreateInternetGateway) || ($.eventName = DeleteInternetGateway) || ($.eventName = DetachInternetGateway) }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_s3_bucket_policy_changes" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "s3_bucket_policy_changes"
  alarm_description = "S3 Bucket Policy Changes Occured"
  metric_name       = "S3BucketPolicyChanges"
  namespace         = "LogMetrics"
  pattern           = "{ ($.eventSource = s3.amazonaws.com) && (($.eventName = PutBucketAcl) || ($.eventName = PutBucketPolicy) || ($.eventName = PutBucketCors) || ($.eventName = PutBucketLifecycle) || ($.eventName = PutBucketReplication) || ($.eventName = DeleteBucketPolicy) || ($.eventName = DeleteBucketCors) || ($.eventName = DeleteBucketLifecycle) || ($.eventName = DeleteBucketReplication)) }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_cloudtrail_configuration_changes" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "cloudtrail_configuration_changes"
  alarm_description = "CloudTrail Configuration Changes Occured"
  metric_name       = "CloudTrailConfigurationChanges"
  namespace         = "LogMetrics"
  pattern           = "{($.eventName = CreateTrail) || ($.eventName = UpdateTrail) || ($.eventName = DeleteTrail) || ($.eventName = StartLogging) || ($.eventName = StopLogging) }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_iam_policy_changes" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "iam_policy_changes"
  alarm_description = "IAM Policy Changes Occured"
  metric_name       = "IAMPolicyChanges"
  namespace         = "LogMetrics"
  pattern           = "{ ($.eventName = DeleteGroupPolicy) || ($.eventName = DeleteRolePolicy) || ($.eventName = DeleteUserPolicy) || ($.eventName = PutGroupPolicy) || ($.eventName = PutRolePolicy) || ($.eventName = PutUserPolicy) || ($.eventName = CreatePolicy) || ($.eventName = DeletePolicy) || ($.eventName = CreatePolicyVersion) || ($.eventName = DeletePolicyVersion) || ($.eventName = AttachRolePolicy) || ($.eventName = DetachRolePolicy) || ($.eventName = AttachUserPolicy) || ($.eventName = DetachUserPolicy) || ($.eventName = AttachGroupPolicy) || ($.eventName = DetachGroupPolicy) }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_root_account_usage" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "root_account_usage"
  alarm_description = "Root Account Usage Occured"
  metric_name       = "RooAccountUsage"
  namespace         = "LogMetrics"
  pattern           = "{ $.userIdentity.type = \"Root\" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != \"AwsServiceEvent\" }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}

module "sns_unauthorized_api_calls" {
  source = "../modules/aws_resource_change_alarm"

  alarm_name        = "unauthorized_api_calls"
  alarm_description = "Unauthorized API Calls Occured"
  metric_name       = "UnauthorizedApiCalls"
  namespace         = "LogMetrics"
  pattern           = "{ ($.errorCode = \"*UnauthorizedOperation\") || ($.errorCode = \"AccessDenied*\") }"
  sns_topic         = aws_sns_topic.sns_resource_changes.arn
}



