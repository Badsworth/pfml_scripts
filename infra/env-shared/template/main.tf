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
      "reductions/dia/*",
      "reductions/dua/*"
    ]
  }]
  pfmldata_bucket_resource_prefixes = flatten([
    for b in local.pfmldata_bucket_resources : [
      for r in b.resource_prefixes : "${b.bucket_arn}/${r}" if length(regexall("\\/\\*$", r)) > 0
    ]
  ])

  ################################################################
  # Configures API gateway resources authorized for S3 operations
  # under the /files endpoint. 
  #
  # Top level keys are used in parts of various resource names.
  #   aws_iam_role: "massgov-pfml-{env}-reductions-dia-files-api-gateway-executor"
  #   aws_iam_role_policy: "massgov-pfml-{env}-reductions-dia-files-executor-role-policy"
  #   ...
  # bucket: ARN of bucket
  # object_prefix: Limits objects available in the bucket that begin with
  #   the specified prefix.
  # resource_name: Namespace for the endpoint used in the API path. 
  #   If the resource_name is "dia", then base path for this endpoint 
  #   will be "/files/dia"
  #
  endpoints = {
    "reductions-dia" = {
      bucket        = data.aws_s3_bucket.agency_transfer.arn,
      object_prefix = "reductions/dia/"
      resource_name = "dia"
    }
    "reductions-dua" = {
      bucket        = data.aws_s3_bucket.agency_transfer.arn,
      object_prefix = "reductions/dua/"
      resource_name = "dua"
    }
  }
}
