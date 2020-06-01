locals {
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # as specified in the infra/pfml-aws/acm.tf file.
  cert_domain = var.environment_name == "prod" ? "paidleave.mass.gov" : "paidleave-test.mass.gov"
  domain      = var.environment_name == "prod" ? "paidleave.mass.gov" : "paidleave-${var.environment_name}.mass.gov"
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
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # as specified in the infra/pfml-aws/acm.tf file.
  domain      = local.cert_domain
  statuses    = ["ISSUED"]
  most_recent = true
}
