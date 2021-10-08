provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

terraform {
  required_version = "0.14.7"
}

module "constants" {
  source = "../../constants"
}

locals {
  # This adds a header so Swagger UI knows where to find UI files on the server.
  #
  # For non-custom domain names, we're relying on the API Gateway-provided URL
  # which serves the API under the "/<env_name>" subpath.
  forwarded_path = local.cert_domain == null ? "'/${var.environment_name}/api/'" : "'/api/'"
  constants_env  = var.is_adhoc_workspace ? "adhoc" : var.environment_name

  # Defines the resources that are available to the pfmldata S3 proxy
  pfmldata_bucket_resources = length(var.pfmldata_bucket_resources) > 0 ? var.pfmldata_bucket_resources : [{
    bucket_arn = data.aws_s3_bucket.agency_transfer.arn
    resource_prefixes = [
      "reductions/dia/",
      "reductions/dia/*",
      "reductions/dua/",
      "reductions/dua/*"
    ]
  }]
  pfmldata_bucket_resource_prefixes = flatten([
    for b in local.pfmldata_bucket_resources : [
      for r in b.resource_prefixes : "${b.bucket_arn}/${r}" if length(regexall("\\/\\*$", r)) > 0
    ]
  ])
}
