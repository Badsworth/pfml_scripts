output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.portal_web_distribution.id
  description = "Cloudfront distribution id for portal environment. Used for cache invalidation in GitHub workflow."
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.claimants_pool.id
}

output "cognito_user_pool_client_id" {
  value = aws_cognito_user_pool_client.massgov_pfml_client.id
}
