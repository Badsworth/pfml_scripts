locals {
  domains = {
    (var.environment_name) = "paidleave-${var.environment_name}.mass.gov"
    "prod"                 = "paidleave.mass.gov"
  }
  cert_domain = var.enable_pretty_domain ? module.constants.cert_domains[var.environment_name] : null
  domain      = lookup(local.domains, var.environment_name)
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
data "aws_acm_certificate" "domain" {
  count = var.enable_pretty_domain ? 1 : 0
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # as specified in the infra/pfml-aws/acm.tf file.
  domain      = local.cert_domain
  statuses    = ["ISSUED"]
  most_recent = true
}
