locals {
  oncall_rotation_api_engineers = [data.pagerduty_user.mass_pfml["Kevin Yeh"].id]
  oncall_rotation_api_delivery  = [data.pagerduty_user.mass_pfml["Allison Johnson"].id]
}
