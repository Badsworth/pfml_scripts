#!/bin/bash
###
#
# This file queries CypressTestResult for the list of failed specs based on environment
# and specific runId
#
# GHA Outputs:
#   failed_specs: string of failed specs seperated by comma.
#   Ex: "cypress/specs/unstable/api_medical_continuous_approval_paymentStatus.ts"
#   Ex: (multiple) "cypress/specs/stable/scenario/portal_bonding_intermittent_approval_pastPayments60K.ts,cypress/specs/stable/scenario/fineos_caring_continuous_denial_appealNotification.ts"
#   failed_specs_count: number/count of failed specs
###

USAGE="
Quieres NR to get list of failed specs based on runId

args:
ENVIRONMENT: The name of the PFML environment to check against.
TEST_RUN_ID: runId of the triggered run

example:
./get-list-failed-specs.sh stage EOLWD/pfml-2055181577-1
"

if [ "$#" -ne 2 ]; then
    echo "$USAGE"
    exit 1
fi

ENVIRONMENT=$1
TEST_RUN_ID=$2
QUERY="SELECT uniques(file) AS 'filename' FROM TestResult WHERE runId = '$TEST_RUN_ID' AND status = 'failed' AND environment = '$ENVIRONMENT' SINCE 1 day AGO UNTIL NOW"

failed_specs_raw=$(newrelic nrql query --query "$QUERY")
# Get list of failed specs from stable group only
failed_specs_formatted=$(echo $failed_specs_raw | jq -r -e '[.[0].filename[] | select(contains("cypress/specs/stable/"))] | join(",")')
failed_specs_count=$(echo $failed_specs_raw | jq -r -e '[.[0].filename[] | select(contains("cypress/specs/stable/"))] | length')
echo "::set-output name=failed_specs::$failed_specs_formatted"
echo "::set-output name=failed_specs_count::$failed_specs_count"
