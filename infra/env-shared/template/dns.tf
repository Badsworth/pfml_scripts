locals {
  domain = "${var.domain_name}.navateam.com"
}

data "aws_acm_certificate" "domain" {
  # ACM certs have to be in us-east-1 to be used with CloudFront
  provider = aws.us-east-1

  # you cannot lookup certs by a SAN, so we lookup based on the TLD with the
  # assumption it also has a wildcard cert as a SAN
  domain      = "navateam.com"
  statuses    = ["ISSUED"]
  most_recent = true
}

resource "aws_api_gateway_domain_name" "domain_name" {
  certificate_arn = data.aws_acm_certificate.domain.arn
  domain_name     = local.domain
}

data "aws_route53_zone" "tld" {
  name = "navateam.com"
}

resource "aws_route53_record" "root_v4" {
  zone_id = data.aws_route53_zone.tld.zone_id
  name    = local.domain
  type    = "A"

  alias {
    name    = aws_api_gateway_domain_name.domain_name.cloudfront_domain_name
    zone_id = aws_api_gateway_domain_name.domain_name.cloudfront_zone_id

    evaluate_target_health = false
  }
}

resource "aws_route53_record" "root_v6" {
  zone_id = data.aws_route53_zone.tld.zone_id
  name    = local.domain
  type    = "AAAA"

  alias {
    name    = aws_api_gateway_domain_name.domain_name.cloudfront_domain_name
    zone_id = aws_api_gateway_domain_name.domain_name.cloudfront_zone_id

    evaluate_target_health = false
  }
}
