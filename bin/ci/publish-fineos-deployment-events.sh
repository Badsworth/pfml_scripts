#!/bin/bash
###
#
# Maintain `CustomDeploymentMarker` events in New Relic by polling for the last seen Fineos version.
#
# There is a NR Synthetic check that scrapes the version information off of the Fineos UI. The version
# is captured as an attribute of the SyntheticCheck event. In this script, we poll for the last seen
# version that synthetic script has encountered, and compare it to records in a CustomDeploymentMarker
# NR event "table".
#
# If the SyntheticCheck reports a version that doesn't match what's in the CustomDeploymentMarker for
# the environment, we create a new CustomDeploymentMarker event and trigger any followup actions by
# setting the GHA output.
#
# GHA Outputs:
#   was_deployed: string "true" or "false" indicating whether a deployment was detected.
#   version: version string of whatever was last seen in Fineos.
###

USAGE="
Maintains CustomDeploymentMarker events for Fineos based on collected synthetic data.

args:
ENVIRONMENT: The name of the PFML environment to check against.

example:
./publish-fineos-deployment-events.sh stage
"
if [[ -z "$1" ]]; then
  echo "$USAGE"
  exit 1
fi

environment=$1

# Collect information about the last stored deployment for this environment in New Relic.
last_stored=$(newrelic nrql query --query "SELECT latest(version) AS version, latest(timestamp) AS timestamp FROM CustomDeploymentMarker WHERE environment = '$environment' AND component = 'fineos' AND version IS NOT NULL SINCE 6 months ago")
last_stored_version=$(echo $last_stored | jq -r -e ".[0].version")

# Collect information about the last version we saw in a synthetic.
last_synthetic=$(newrelic nrql query --query "SELECT latest(custom.fineos_version) AS version, latest(timestamp) AS timestamp FROM SyntheticCheck WHERE custom.environment = '$environment' AND custom.fineos_version IS NOT NULL SINCE 1 day ago")
last_synthetic_version=$(echo $last_synthetic | jq -r -e ".[0].version")

# Ensure that we have a Fineos version logged in the last 24 hours before trying to write a deployment.
if [[ "$?" -ne 0 ]]; then
  echo "Failed to fetch the last synthetic record for the $environment environment. Are you sure there are records containing a Fineos version in the last 24 hours?"
  exit 1
fi

echo "::set-output name=version::$last_synthetic_version"
# Compare the two and write the event if there's a mismatch.
if [[ "$last_stored_version" != "$last_synthetic_version" ]]; then
  # Create a new deployment event.
  echo "Publishing a deployment event for $last_synthetic_version because it was seen more recently than $last_stored_version"
  echo "::set-output name=was_deployed::true"
  newrelic events post --event "{ \"eventType\": \"CustomDeploymentMarker\", \"component\": \"fineos\", \"environment\":\"$environment\", \"version\": \"$last_synthetic_version\" }"
else
  echo "No new deployments to $environment."
  echo "::set-output name=was_deployed::false"
fi

