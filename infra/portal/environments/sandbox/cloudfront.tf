provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

data "aws_acm_certificate" "domain" {
  # ACM certs have to be in us-east-1 to be used with CloudFront
  provider = aws.us-east-1

  # you cannot lookup certs by a SAN, so we lookup based on the TLD with the
  # assumption it also has a wildcard cert as a SAN
  domain      = local.tld
  statuses    = ["ISSUED"]
  most_recent = true
}

# DNS
data "aws_cloudfront_distribution" "portal_web_distribution" {
  id = module.massgov_pfml.cloudfront_distribution_id
}

data "aws_route53_zone" "tld" {
  name = local.tld
}

resource "aws_route53_record" "root_v4" {
  zone_id = data.aws_route53_zone.tld.zone_id
  name    = local.domain
  type    = "A"

  alias {
    name    = data.aws_cloudfront_distribution.portal_web_distribution.domain_name
    zone_id = data.aws_cloudfront_distribution.portal_web_distribution.hosted_zone_id

    evaluate_target_health = false
  }
}

resource "aws_route53_record" "root_v6" {
  zone_id = data.aws_route53_zone.tld.zone_id
  name    = local.domain
  type    = "AAAA"

  alias {
    name    = data.aws_cloudfront_distribution.portal_web_distribution.domain_name
    zone_id = data.aws_cloudfront_distribution.portal_web_distribution.hosted_zone_id

    evaluate_target_health = false
  }
}
