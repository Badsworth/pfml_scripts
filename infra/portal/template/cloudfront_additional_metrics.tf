
resource "null_resource" "cloudfront_addtional_metrics" {

 provisioner "local-exec" {
   command = "aws cloudfront create-monitoring-subscription --distribution-id $cloudfront_distribution_id --monitoring-subscription RealtimeMetricsSubscriptionConfig={RealtimeMetricsSubscriptionStatus=Enabled}"

   environment = {
      cloudfront_distribution_id = aws_cloudfront_distribution.portal_web_distribution.id
      }
  }

  triggers = {
    "timeStamp" = timestamp()
  }
}