#!/usr/bin/env bash
set -euo pipefail

USAGE="
Deletes the history for a Github Actions workflow and removes it from the UI. Requires hub (https://hub.github.com/).

args:
FILENAME: name of the workflow file.

example:
./delete-workflow.sh tenable-test.yml
"

if [[ $# != 1 ]]; then
    echo "$USAGE"
    exit 1
fi

filename=$1

workflow_data=$(hub api repos/EOLWD/pfml/actions/workflows | jq ".workflows | .[] | select( .path == \".github/workflows/$filename\" )")

workflow_id=$(echo $workflow_data | jq ".id" | head -1)

if [ -z workflow_id ]; then
    echo "Workflow not found."
    exit 1
fi

echo "Found workflow ID: $workflow_id"
echo $workflow_data | jq
echo

run_ids=$(hub api repos/EOLWD/pfml/actions/workflows/$workflow_id/runs | jq '.workflow_runs | .[] | .id')

echo "The following runs will be permanently deleted:"
echo $run_ids
echo

read -p "Are you sure you want to delete these runs? (y/n) " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi

echo

for run_id in $run_ids; do
    echo "Deleting $run_id"
    hub api repos/EOLWD/pfml/actions/runs/$run_id -X DELETE
done

echo "Done!"
