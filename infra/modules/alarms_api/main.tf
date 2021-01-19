module "constants" {
  source = "../../constants"
}

locals {
  app_name                     = "pfml-api"
  newrelic_account_id          = "2837112" # PFML's New Relic sub-account number
  newrelic_trusted_account_key = "1606654" # EOLWD's New Relic parent account number
}
