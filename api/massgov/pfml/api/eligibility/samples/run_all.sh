#!/usr/bin/env bash
#
# Run various financial eligibility scenarios.
#

API=http://localhost:1550/v1/financial-eligibility

for f in *.json
do
  echo =============== $f ===============
  cat "$f"
  echo "==>"
  curl --silent \
       --header "Authorization: Bearer $TOKEN" \
       --header "Accept: application/json" \
       --header "Content-Type: application/json" \
       --data @$f \
       "$API" \
    | json_pp
  echo
done
