resource "aws_cloudwatch_log_subscription_filter" "rds_lambdafunction_logfilter" {
  name           = "RDS_Enhanced_Metrics_to_New_Relic"
  log_group_name = "RDSOSMetrics"
  filter_pattern = "{ $.instanceID = \"massgov-pfml-*\" }"
  // Hard coded bc this function is managed by AWS SAM for now
  destination_arn = module.constants.newrelic_log_ingestion_arn
}


