locals {
  cert_domain = module.constants.cert_domains[var.environment_name]
  api_domain  = var.environment_name == "prod" ? "paidleave-api.mass.gov" : "paidleave-api-${var.environment_name}.mass.gov"
}

// NOTE: These must be requested through the AWS Console instead of terraform in order
//       to properly do an MX lookup for the EOTSS emails that need to receive the validation requests.
//
// These should have the following SANs based on the domain name:
//
// domain_name: paidleave.mass.gov
// SANS: paidleave-api.mass.gov
//
// domain_name: paidleave-test.mass.gov
// SANs: paidleave-stage.mass.gov,
//       paidleave-api-test.mass.gov,
//       paidleave-api-stage.mass.gov
//
// domain_name: paidleave-performance.mass.gov
// SANs: paidleave-training.mass.gov,
//       paidleave-api-performance.mass.gov,
//       paidleave-api-training.mass.gov
//
data "aws_acm_certificate" "domain" {
  count       = var.enable_pretty_domain ? 1 : 0
  domain      = local.cert_domain
  statuses    = ["ISSUED"]
  most_recent = true
}

resource "aws_api_gateway_domain_name" "domain_name" {
  count           = var.enable_pretty_domain ? 1 : 0
  certificate_arn = data.aws_acm_certificate.domain[0].arn
  domain_name     = local.api_domain
}

resource "aws_api_gateway_base_path_mapping" "stage_mapping" {
  count       = var.enable_pretty_domain ? 1 : 0
  stage_name  = var.environment_name
  api_id      = aws_api_gateway_rest_api.pfml.id
  domain_name = aws_api_gateway_domain_name.domain_name[0].domain_name
}
