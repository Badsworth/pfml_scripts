locals {
  cert_domain = lookup(module.constants.cert_domains, var.environment_name)
  domain      = lookup(module.constants.domains, var.environment_name)
}

// NOTE: These must be requested through the AWS Console instead of terraform in order
//       to properly do an MX lookup for the EOTSS emails that need to receive the validation requests.
//
// These should have the following SANs based on the domain name, e.g.:
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
  count       = local.cert_domain == null ? 0 : 1
  domain      = local.cert_domain
  statuses    = ["ISSUED"]
  most_recent = true
}
