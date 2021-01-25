# NewRelic Entity file for API Alarms 

data "newrelic_entity" "pfml-api" {
  # A reference to the API's top-level object in New Relic. Not managed by TF, but required by other Terraform objects.
  name   = "${upper(local.app_name)}-${upper(var.environment_name)}"
  domain = "APM"
  type   = "APPLICATION"
}

data "aws_db_instance" "default" {
  db_instance_identifier = "massgov-pfml-${var.environment_name}"
}