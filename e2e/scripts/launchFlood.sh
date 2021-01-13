#!/bin/bash
set -e

while getopts ":u:l:p:n:v:t:m:d:i:q:r:y:s:" opt; do
  case $opt in
    u) TOKEN="$OPTARG"
    ;;
    l) TOOL="$OPTARG"
    ;;
    p) PROJECT="$OPTARG"
    ;;
    n) NAME="$OPTARG"
    ;;
    v) PRIVACY="$OPTARG"
    ;;
    t) THREADS="$OPTARG"
    ;;
    m) RAMPUP="$OPTARG"
    ;;
    d) DURATION="$OPTARG"
    ;;
    i) INFRA="$OPTARG"
    ;;
    q) QUANTITY="$OPTARG"
    ;;
    r) REGION="$OPTARG"
    ;;
    y) TYPE="$OPTARG"
    ;;
    s) STOP="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# Check we have the jq binary to make parsing JSON responses a bit easier
command -v jq >/dev/null 2>&1 || \
{ echo >&2 "Please install http://stedolan.github.io/jq/download/  Aborting."; exit 1; }

# Start a flood
echo "[$(date +%FT%T)+00:00] Starting flood"
UUID=$(curl -u $TOKEN: \
-X POST https://api.flood.io/floods \
-F "flood[tool]=$TOOL" \
-F "flood[project]=$PROJECT" \
-F "flood[name]=$NAME" \
-F "flood[privacy_flag]=$PRIVACY" \
-F "flood[threads]=$THREADS" \
-F "flood[rampup]=$RAMPUP" \
-F "flood[duration]=$DURATION" \
-F "flood_files[]=@./scripts/index.perf.ts" \
-F "flood_files[]=@./scripts/floodBundle.zip" \
-F "flood[grids][][infrastructure]=$INFRA" \
-F "flood[grids][][instance_quantity]=$QUANTITY" \
-F "flood[grids][][region]=$REGION" \
-F "flood[grids][][instance_type]=$TYPE" \
-F "flood[grids][][stop_after]=$STOP" | jq -r ".uuid")
echo $UUID
