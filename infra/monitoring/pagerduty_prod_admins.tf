# Schedule and Escalation notifications for the on-call prod admin.
#
resource "pagerduty_schedule" "mass_pfml_prod_admin" {
  name      = "Mass PFML Production Admin"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Production Admin"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-10-28T13:00:00-05:00"
    rotation_turn_length_seconds = 604800 # 1 week
    users                        = [data.pagerduty_user.mass_pfml["Kevin Yeh"].id]
  }
}

#  Production Admin
#  --> no acknowledgement after 5 min --> Production Admin (again)
#  --> no acknowledgement after 5 min --> repeat
#
resource "pagerduty_escalation_policy" "mass_pfml_prod_admin" {
  name      = "Mass PFML Production Admin"
  num_loops = 2

  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_prod_admin.id
    }
  }

  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_prod_admin.id
    }
  }
}
