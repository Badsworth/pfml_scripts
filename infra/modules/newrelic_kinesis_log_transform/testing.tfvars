kinesis_firehose_name = "massgov-pfml-sms-newrelic"
dlq_bucket_name       = "massgov-pfml-sms-kinesis-to-newrelic-dlq"
function_name         = "kinesis_firehose_sms_lambda"
function_description  = "Kinesis filter to mask sms destinations before sending to newrelic"
source_file_path      = "."
nr_log_group_name     = "sns/us-east-1/498823821309/DirectPublishToPhoneNumber"
cw_log_group_names = [
  "sns/us-east-1/498823821309/DirectPublishToPhoneNumber",
  "sns/us-east-1/498823821309/DirectPublishToPhoneNumber/Failure"
]
