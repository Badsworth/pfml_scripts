#!/usr/bin/env bash
#
# Script for generating Terraform variables that should use last deployed value
# by default.
#
set -euo pipefail

USAGE="
Usage: Generates a variable whose value is automatically filled in with last deployed value

$(basename $0) COMPONENT VAR_NAME VAR_DESCRIPTION

args:
  COMPONENT - The component to bootstrap (portal|api|env-shared)
  VAR_NAME - The Terraform variable name to generate template for
  VAR_DESCRIPTION - The description for the Terraform variable

example:
  $(basename $0) api service_x_tag 'Deployment tag for service X'

This does not set up the variable for all environments, run the bootstrap script
or copy into place manually (updating \$ENV_NAME as appropriate).
"

if [[ $# != 3 ]]; then
    echo "$USAGE"
    exit 1
fi

COMPONENT=$1
VAR_NAME=$2
VAR_DESCRIPTION=$3

SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

source $SCRIPT_PATH/../shab

generate_var () {
    DEST=$SCRIPT_PATH/$COMPONENT/$VAR_NAME.tf

    shab $SCRIPT_PATH/make-auto-variable.tf.template > $DEST
}

generate_var
