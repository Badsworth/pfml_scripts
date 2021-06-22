# # Data objects to reference lambdas defined in the API Terraform.


# # Refer to these lambdas by their most_recent aliases (for provisioned concurrency) in perf and prod.
# data "aws_lambda_alias" "cognito_post_confirmation__latest" {
#   count         = var.cognito_enable_provisioned_concurrency ? 1 : 0
#   function_name = "massgov-pfml-${var.environment_name}-cognito_post_confirmation"
#   name          = "most_recent"
# }

# data "aws_lambda_alias" "cognito_pre_signup__latest" {
#   count         = var.cognito_enable_provisioned_concurrency ? 1 : 0
#   function_name = "massgov-pfml-${var.environment_name}-cognito_pre_signup"
#   name          = "most_recent"
# }


# # Keep direct handles to the $LATEST versions of these lambdas in test, stage, and train.
# data "aws_lambda_function" "cognito_post_confirmation" {
#   count         = var.cognito_enable_provisioned_concurrency ? 0 : 1
#   function_name = "massgov-pfml-${var.environment_name}-cognito_post_confirmation"
#   qualifier     = "$LATEST"
# }

# data "aws_lambda_function" "cognito_pre_signup" {
#   count         = var.cognito_enable_provisioned_concurrency ? 0 : 1
#   function_name = "massgov-pfml-${var.environment_name}-cognito_pre_signup"
#   qualifier     = "$LATEST"
# }
