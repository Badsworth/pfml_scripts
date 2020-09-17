output "common_tags" {
  value = {
    # TODO: Change to DFML once a value exists in the standards
    agency = "eol"
    # TODO: Change to PFML application once a value exists in the standards
    application   = "coreinf"
    businessowner = "ma-pfml-alerts@mass.gov"
    createdby     = "ma-pfml-alerts@mass.gov"
    itowner       = "ma-pfml-alerts@mass.gov"
    secretariat   = "eolwd"
  }
}

output "newrelic_log_ingestion_arn" {
  value = "arn:aws:lambda:us-east-1:498823821309:function:newrelic-log-ingestion"
}
