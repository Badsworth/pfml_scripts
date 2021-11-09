# Define services, teams, schedules, and escalation policies for the API team.
#
# Services and Escalation Policies:
#   Mass PFML API (Low Priority)
#   Mass PFML API (High Priority)
#
# Schedules:
#   Mass PFML API Eng Primary
#   Mass PFML API Eng Secondary
#   Mass PFML API Delivery Manager
#
resource "pagerduty_team" "mass_pfml_api" {
  name        = "Mass PFML API"
  description = "Mass PFML API Team"
}

resource "pagerduty_service" "mass_pfml_api_low_priority" {
  name                    = "Mass PFML API (Low Priority)"
  auto_resolve_timeout    = 604800 # Auto-resolve after 7 days if left open
  acknowledgement_timeout = 86400  # Require re-acknowledgement after 24 hours
  escalation_policy       = pagerduty_escalation_policy.mass_pfml_api_low_priority.id
  alert_creation          = "create_alerts_and_incidents"

  incident_urgency_rule {
    type    = "constant"
    urgency = "low"
  }
}

resource "pagerduty_service" "mass_pfml_api_high_priority" {
  name                    = "Mass PFML API (High Priority)"
  auto_resolve_timeout    = 604800 # Auto-resolve after 7 days if left open
  acknowledgement_timeout = 7200   # Require re-acknowledgement after 2 hours
  escalation_policy       = pagerduty_escalation_policy.mass_pfml_api_high_priority.id
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

resource "pagerduty_schedule" "mass_pfml_api_primary" {
  name      = "Mass PFML API Eng Primary"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [teams, layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Primary Engineer"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-10-28T13:00:00-05:00"
    rotation_turn_length_seconds = 604800 # 1 week
    users                        = [data.pagerduty_user.mass_pfml["Kevin Yeh"].id]
  }
}

resource "pagerduty_schedule" "mass_pfml_api_secondary" {
  name      = "Mass PFML API Eng Secondary"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [teams, layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Secondary Engineer"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-11-04T13:00:00-05:00"
    rotation_turn_length_seconds = 604800 # 1 week
    users                        = [data.pagerduty_user.mass_pfml["Kevin Yeh"].id]
  }
}

resource "pagerduty_schedule" "mass_pfml_api_delivery" {
  name      = "Mass PFML API Delivery Manager"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [teams, layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Delivery Manager"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-11-04T13:00:00-05:00"
    rotation_turn_length_seconds = 1209600 # 2 weeks
    users                        = [data.pagerduty_user.mass_pfml["Allison Johnson"].id]
  }
}

// Rotation for onboarding engineers by shadowing the current primary on-call.
//
// If you need the shadow rotation, set the local variable to true. After the change is merged,
// go into Pagerduty and manually set overrides for the week that they are supposed to onboard.
// 
// When not in use, please disable this by setting the local variable to false.
//
locals {
  enable_shadow_rotation = false
}

resource "pagerduty_schedule" "mass_pfml_api_primary_shadow" {
  count     = local.enable_shadow_rotation ? 1 : 0
  name      = "Mass PFML API Eng Primary (SHADOW)"
  time_zone = "America/New_York"

  // Ignore changes to users and start times, which we expect to be adjusted
  // through the UI by delivery managers and other team members.
  lifecycle {
    ignore_changes = [teams, layer[0].users, layer[0].rotation_virtual_start, layer[0].start]
  }

  layer {
    name                         = "Primary (SHADOW) Engineer"
    start                        = "2020-11-04T13:00:00-05:00"
    rotation_virtual_start       = "2020-10-28T13:00:00-05:00"
    rotation_turn_length_seconds = 604800 # 1 week
    users                        = [data.pagerduty_user.mass_pfml["Kevin Yeh"].id]
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
resource "pagerduty_escalation_policy" "mass_pfml_api_high_priority" {
  name      = "Mass PFML API (High Priority)"
  num_loops = 2
  teams     = [pagerduty_team.mass_pfml_api.id]

  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_api_primary.id
    }

    // Optionally add the Primary Shadow to the escalation rule, if the shadow rotation is enabled.
    dynamic "target" {
      for_each = local.enable_shadow_rotation ? [1] : []
      content {
        type = "schedule_reference"
        id   = pagerduty_schedule.mass_pfml_api_primary_shadow[0].id
      }
    }
  }

  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_api_primary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_api_secondary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_api_delivery.id
    }
  }
}

# Low Priority:
#
#  Primary Engineer
#  --> no acknowledgement after 10 min --> Secondary Engineer
#  --> no acknowledgement after 10 min --> repeat
#
resource "pagerduty_escalation_policy" "mass_pfml_api_low_priority" {
  name      = "Mass PFML API (Low Priority)"
  num_loops = 2
  teams     = [pagerduty_team.mass_pfml_api.id]

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_api_primary.id
    }

    // Optionally add the Primary Shadow to the escalation rule, if the shadow rotation is enabled.
    dynamic "target" {
      for_each = local.enable_shadow_rotation ? [1] : []
      content {
        type = "schedule_reference"
        id   = pagerduty_schedule.mass_pfml_api_primary_shadow[0].id
      }
    }
  }

  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.mass_pfml_api_secondary.id
    }
  }
}
