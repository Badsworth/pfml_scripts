output "common_tags" {
  value = {
    agency        = "dfml"
    application   = "pfml"
    businessowner = "ma-pfml-alerts@mass.gov"
    createdby     = "ma-pfml-alerts@mass.gov"
    itowner       = "ma-pfml-alerts@mass.gov"
    secretariat   = "eolwd"
  }
}

output "newrelic_log_ingestion_arn" {
  value = "arn:aws:lambda:us-east-1:498823821309:function:newrelic-log-ingestion"
}

# Mapping of different environments/VPCs to resource tags
output "environment_tags" {
  value = {
    "test"        = "test"
    "stage"       = "stage"
    "prod"        = "prod"
    "nonprod"     = "stage"
    "performance" = "qa"
    "training"    = "train"
  }
}
