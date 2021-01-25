locals {
  oncall_rotation_portal_engineers = [data.pagerduty_user.mass_pfml["Sheldon Bachstein"].id]
  oncall_rotation_portal_delivery  = [data.pagerduty_user.mass_pfml["Jim Delloso"].id]
}
