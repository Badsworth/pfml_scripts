#!/bin/bash

# This script checks the /v1/status endpoint of the mass-pfml-api for a healthy state.
# It reties the check as many times as is configured via the $1 argument after which it exits
# with a failure.

retries=$1
try=1 ; while [[ $try -le $retries ]] ; do
    status=$(./bin/check_container_health.py)
    if [[ $status == '200' ]]; then
        echo "Container is in a healthy state."
        exit 0
    fi
    sleep 1
    echo "Retry: #${try} / state: ${status}"
    ((try = try + 1))

done
if [[ $status != '200' ]]; then
    echo "Container is in an unhealthy state."
    exit 1
fi
echo "Container is in an unresponsive state."
exit 1