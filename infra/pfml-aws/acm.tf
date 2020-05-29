resource "aws_acm_certificate" "pfml-nonprod" {
  domain_name = "paidleave-test.mass.gov"

  subject_alternative_names = [
    "paidleave-api-test.mass.gov",
    "paidleave-stage.mass.gov",
    "paidleave-api-stage.mass.gov"
  ]

  validation_method = "EMAIL"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate" "pfml-prod" {
  domain_name = "paidleave.mass.gov"

  subject_alternative_names = [
    "paidleave-api.mass.gov"
  ]

  validation_method = "EMAIL"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "nonprod" {
  certificate_arn = aws_acm_certificate.pfml-nonprod.arn
}

resource "aws_acm_certificate_validation" "prod" {
  certificate_arn = aws_acm_certificate.pfml-prod.arn
}
