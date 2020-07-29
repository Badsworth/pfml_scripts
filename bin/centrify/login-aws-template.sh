#!/usr/bin/env bash
#
# Script for generating a temporary AWS access key through Centrify login.
#
# Note that this script needs to be installed with the Centrify AWS CLI files using the
# install-centrify-aws-cli.sh script, and cannot be run directly as provided in pfml/bin.
#
set -euo pipefail
GREP_OPTIONS=

python3 -c "import requests, boto3, colorama" || (
    echo "Python dependencies are not installed. Please install and re-run this script."
    echo "e.g. pip3 install --user requests boto3 colorama"
    exit 1
)

# Make sure AWS_PROFILE is set to some (any!) defined profile.
# This is a requirement/workaround for the centrify/aws script.
# This does not export the changes into the caller's shell.
mkdir -p ~/.aws/

if ! [[ -f '~/.aws/credentials' ]]; then
   touch ~/.aws/credentials
fi

# Store the existing AWS_PROFILE for informative messaging later.
PREV_AWS_PROFILE=${AWS_PROFILE:-}

get_last_aws_profile () {
    grep '\[[^]]*\]' ~/.aws/credentials | tail -1
}

create_credentials_file () {
  cat <<INNER >> ~/.aws/credentials
[default]
region = us-east-1
INNER

  echo default    
}

profile=$(get_last_aws_profile || create_credentials_file)
AWS_PROFILE=$(echo $profile | tr -d '[]')

# Start interactive login by using the current directory's python environment
# and changing to the correct dir at script runtime.
#
# Make sure we're in the script's directory, since it relies on SSL certificate files in here.
# Grab the absolute path of this script, e.g. /home/user/centrify-aws-cli-utilities/Python-AWS
#
# I know, this is hacky. pls don't judge me.
#
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

python3 -c "
import os
import sys
os.chdir(\"$SCRIPT_PATH\")
sys.argv.append('-tenant')
sys.argv.append('eotss.my.centrify.com')
sys.argv.append('-r')
sys.argv.append('us-east-1')
import CentrifyAWSCLI
"

# Grab the AWS profile name from the credentials file and print an export command for convenience.
AWS_PROFILE=$(grep AWS-498823821309 ~/.aws/credentials | tail -1 | tr -d '[]')

# If AWS_PROFILE is not already set to the EOTSS role, print an informative message.
if [[ "$PREV_AWS_PROFILE" != "$AWS_PROFILE" ]]; then
    echo
    echo "AWS_PROFILE is currently: ${PREV_AWS_PROFILE:-not set}. Run the following command to set it:"
    echo "export AWS_PROFILE=$AWS_PROFILE"
fi
