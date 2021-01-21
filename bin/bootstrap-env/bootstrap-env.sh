#!/usr/bin/env bash
#
# Script for setting up components in a new environment.
#
# This does not set up the actual S3 bucket that they
# depend on; to do that, you should go to infra/pfml-aws/s3.tf
# and add the environment to the list at the top, then apply changes.
#
set -euo pipefail

USAGE="
Usage: Bootstraps a component in a new environment.

./bootstrap-env.sh ENV_NAME COMPONENT

args:
  ENV_NAME  - The environment name, e.g. test, stage, prod.
  COMPONENT - The component to bootstrap (portal|api|env-shared)

example:
  ./bootstrap-env.sh test api

This does not set up the actual S3 bucket that components depend on.
To do that, go to infra/pfml-aws/s3.tf and add the environment
to the list at the top, then apply changes.
"

if [[ $# != 2 ]]; then
    echo "$USAGE"
    exit 1
fi

ENV_NAME=$1
COMPONENT=$2

SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
INFRA_PATH=$SCRIPT_PATH/../../infra

source $SCRIPT_PATH/../shab

# Updates the provided component by copying the template
# into the appropriate infra/ directory and replacing $ENV_NAME.
#
update_component () {
    COMPONENT_TEMPLATE_PATH=$SCRIPT_PATH/$COMPONENT
    COMPONENT_PATH=$INFRA_PATH/$COMPONENT/environments/$ENV_NAME

    if ! [ -d $COMPONENT_TEMPLATE_PATH ]; then
        echo "'$COMPONENT' template was not found in $SCRIPT_PATH; exiting."
        exit 1
    fi

    mkdir -p $COMPONENT_PATH

    find "$SCRIPT_PATH/$COMPONENT" -type f | while read -r file; do
        mkdir -p $COMPONENT_PATH$(dirname ${file#"$SCRIPT_PATH/$COMPONENT"})
        shab "$file" > $COMPONENT_PATH${file#"$SCRIPT_PATH/$COMPONENT"};
    done
}

update_component
