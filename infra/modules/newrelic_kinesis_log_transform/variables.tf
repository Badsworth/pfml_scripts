variable "kinesis_firehose_name" {
  description = "The name of the Kinesis Firehose"
  type        = string
}

variable "dlq_bucket_name" {
  description = "The name of the Dead Letter Queue S3 bucket, used when logs not delivered to New Relic"
  type        = string
}

variable "function_name" {
  description = "Lambda function name and source file name, will have .py appended for source file"
  type        = string
}

variable "function_description" {
  description = "Description of Lambda Kinesis Filter Function purpose"
  type        = string
}

variable "source_file_path" {
  description = "Path to Lambda source"
  type        = string
}

variable "nr_log_group_name" {
  description = "Extra parameter to be included with logs to identify your logs in New Relic"
  type        = string
}

variable "cw_log_group_names" {
  description = "List of one or more log groups to add Kinesis Subscription"
  type        = list(string)
}
