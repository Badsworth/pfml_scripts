# Define services, teams, schedules, and escalation policies for the Portal team.
#
# Services and Escalation Policies:
#   Mass PFML Portal (Low Priority)
#   Mass PFML Portal (High Priority)
#
# Schedules:
#   Mass PFML Portal Eng Primary
#   Mass PFML Portal Eng Secondary
#   Mass PFML Portal Delivery Manager
#
resource "pagerduty_team" "mass_pfml_portal" {
  name        = "Mass PFML Portal"
  description = "Mass PFML Portal"
}

resource "pagerduty_service" "mass_pfml_portal_low_priority" {
  name                    = "Mass PFML Portal (Low Priority)"
  auto_resolve_timeout    = 604800 # Auto-resolve after 7 days if left open
  acknowledgement_timeout = 86400  # Require re-acknowledgement after 24 hours
  escalation_policy       = pagerduty_escalation_policy.mass_pfml_portal_low_priority.id
  alert_creation          = "create_alerts_and_incidents"

  incident_urgency_rule {
    type    = "constant"
    urgency = "low"
  }
}

resource "pagerduty_service" "mass_pfml_portal_high_priority" {
  name                    = "Mass PFML Portal (High Priority)"
  auto_resolve_timeout    = 604800 # Auto-resolve after 7 days if left open
  acknowledgement_timeout = 7200   # Require re-acknowledgement after 2 hours
  escalation_policy       = pagerduty_escalation_policy.mass_pfml_portal_high_priority.id
  alert_creation          = "create_alerts_and_incidents"

  incident_urgency_rule {
    type    = "constant"
    urgency = "severity_based"
  }
}

# Pagerduty Schedules (On-Call Roles)
# ###################################
#
# We use the same set of engineers for primary and secondary. We offset the primary
# virtual start schedule so that the engineer roles are staggered -- the primary
# on-call engineer becomes the secondary in the following week.
#
# Primary:   ["B", "C", "A", "B", "C", "A", ...]
# Secondary: ["A", "B", "C", "A", "B", "C", ...]
#

resource "pagerduty_schedule" "mass_pfml_portal_primary" {
  name      = "Mass PFML Portal Eng Primary"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Primary Engineer"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-10-28T13:00:00-05:00"
    rotation_turn_length_seconds = 604800 # 1 week
    users                        = [data.pagerduty_user.mass_pfml["Sheldon Bachstein"].id]
  }
}

resource "pagerduty_schedule" "mass_pfml_portal_secondary" {
  name      = "Mass PFML Portal Eng Secondary"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Secondary Engineer"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-11-04T13:00:00-05:00"
    rotation_turn_length_seconds = 604800 # 1 week
    users                        = [data.pagerduty_user.mass_pfml["Sheldon Bachstein"].id]
  }
}

resource "pagerduty_schedule" "mass_pfml_portal_delivery" {
  name      = "Mass PFML Portal Delivery Manager"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Delivery Manager"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-11-04T13:00:00-05:00"
    rotation_turn_length_seconds = 1209600 # 2 weeks
    users                        = [data.pagerduty_user.mass_pfml["Kevin Toles"].id]
  }
}

# Pagerduty Escalation Policies
# ###################################

# High Priority:
#
#  Primary Engineer
#  --> no acknowledgement after 5 min --> Primary Engineer (re-ping)
#  --> no acknowledgement after 5 min --> Secondary Engineer
#  --> no acknowledgement after 10 min --> Delivery Manager
#  --> no acknowledgement after 10 min --> repeat
#
resource "pagerduty_escalation_policy" "mass_pfml_portal_high_priority" {
  name      = "Mass PFML Portal (High Priority)"
  num_loops = 2
  teams     = [pagerduty_team.mass_pfml_portal.id]

  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_portal_primary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_portal_primary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_portal_secondary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_portal_delivery.id
    }
  }
}

# Low Priority:
#
#  Primary Engineer
#  --> no acknowledgement after 10 min --> Secondary Engineer
#  --> no acknowledgement after 10 min --> repeat
#
resource "pagerduty_escalation_policy" "mass_pfml_portal_low_priority" {
  name      = "Mass PFML Portal (Low Priority)"
  num_loops = 2
  teams     = [pagerduty_team.mass_pfml_portal.id]

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_portal_primary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_portal_secondary.id
    }
  }
}
