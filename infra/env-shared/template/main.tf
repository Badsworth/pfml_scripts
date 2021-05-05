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
}
