locals {
  users = {
    "Kevin Yeh" = {
      email = "kevin@navapbc.com"
    },
    "Allison Johnson" = {
      email = "allisonjohnson@navapbc.com"
    },
    "Sheldon Bachstein" = {
      email = "sheldon@navapbc.com"
    },
    "Keith Fitts" = {
      email = "keith.fitts@mass.gov"
    }
  }
}

# Set up references to PD users who were manually added so we can add seed the PD schedules.
#
# Example Usage:
#
#   data.pagerduty_user.mass_pfml["Kevin Yeh"]
#
data "pagerduty_user" "mass_pfml" {
  for_each = local.users
  email    = each.value.email
}
