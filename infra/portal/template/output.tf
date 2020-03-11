output "cloudfront_distribution_id" {
  value       = "${aws_cloudfront_distribution.portal_web_distribution.id}"
  description = "Cloudfront distribution id for portal environment."
}
