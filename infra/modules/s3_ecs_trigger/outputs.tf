output "lambda_arn" {
  description = "ARN of the generated lambda"
  value       = aws_lambda_function.task_trigger.arn
}
