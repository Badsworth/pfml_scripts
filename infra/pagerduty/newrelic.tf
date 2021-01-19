# Terraform code for managing New Relic secrets from AWS SSM. These are used to configure the NewRelic provider.
# These params have been manually stored in SSM and are not managed through Terraform.
# moved to PD

# Personal API key tied to a single user. NB: replace this key if Ada ever leaves.
data "aws_ssm_parameter" "newrelic-api-key" {
  name = "/admin/pfml-api/newrelic-api-key"
}

data "aws_ssm_parameter" "newrelic-admin-api-key" {
  name = "/admin/pfml-api/newrelic-admin-api-key"
}
