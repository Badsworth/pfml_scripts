#!/usr/bin/env bash
# Script to run migrations within an environment through an ECS task.
#
# This relies on resources and outputs created in infra/api, which should
# be updated prior to running this script.
#
set -o errexit -o pipefail

DIR=$(dirname "${BASH_SOURCE[0]}")

usage() {
  echo "Usage: ./run-task.sh ENV_NAME TASK_NAME [AUTHOR] [COMMAND ...]"
  echo "ex: ./run-task.sh test db-migrate-up first_name.last_name"
  exit 1
}

ENV_NAME=$1
TASK_NAME=$2
shift 2 || usage

if ! [ -z "$CI" ]; then
    AUTHOR=github-actions
else
    AUTHOR=$1
    shift || usage
fi

COMMAND=("$@")

if [ -z "$ENV_NAME" ] || [ -z "$TASK_NAME" ] || [ -z "$AUTHOR" ]; then
  usage
fi


pushd $DIR/../../infra/ecs-tasks/environments/$ENV_NAME
TF_OUTPUTS=$(terraform output -json || (terraform init -lock-timeout=120s && terraform output -json))
popd

NETWORK_CONFIG=$(jq \
    --argjson SUBNETS "$(echo $TF_OUTPUTS | jq .subnets.value)" \
    --argjson SECURITY_GROUPS "$(echo $TF_OUTPUTS | jq .security_groups.value)" \
    '.awsvpcConfiguration.subnets=$SUBNETS |
     .awsvpcConfiguration.securityGroups=$SECURITY_GROUPS' \
    $DIR/network_config.json.tpl)

TASK_DEFINITION="pfml-api-$ENV_NAME-$TASK_NAME"
echo "Task definition $TASK_DEFINITION"

# Construct command overrides as JSON from COMMAND array
COMMAND_JSON=$(printf '%s\n' "${COMMAND[@]}" | jq -R . | jq -s .)
OVERRIDES=$(jq --compact-output \
    --arg TASK_NAME "$TASK_NAME" \
    --argjson COMMAND "$COMMAND_JSON" \
    '.containerOverrides[0].name=$TASK_NAME |
     .containerOverrides[0].command=$COMMAND' \
    $DIR/container_overrides.json.tpl)

# Construct aws command arguments
AWS_ARGS=("--region=us-east-1"
    ecs run-task
    "--cluster=$ENV_NAME"
    "--started-by=$AUTHOR"
    "--task-definition=$TASK_DEFINITION"
    "--launch-type=FARGATE"
    "--platform-version=1.4.0"
    --network-configuration "$NETWORK_CONFIG"
    )

if [ ${#COMMAND[@]} -ne 0 ]
then
  AWS_ARGS+=(--overrides "$OVERRIDES")
fi

echo "Running aws"
printf " ... %s\n" "${AWS_ARGS[@]}"

# Start the ECS task
RUN_TASK=$(aws "${AWS_ARGS[@]}")

echo "Started task:"
echo "$RUN_TASK" | jq .

TASK_ARN=$(echo $RUN_TASK | jq '.tasks[0].taskArn' | sed -e 's/^"//' -e 's/"$//')

aws ecs wait tasks-stopped --region us-east-1 --cluster $ENV_NAME --tasks $TASK_ARN

TASK_STATUS=$(aws ecs describe-tasks --cluster $ENV_NAME --task $TASK_ARN | jq -r '.tasks[]')
EXIT_CODE=$(echo $TASK_STATUS | jq '.containers[].exitCode')

if [ "$EXIT_CODE" == "null" ]; then
  STOPPED_REASON=$(echo "$TASK_STATUS" | jq '.stoppedReason')
  echo "ECS task failed to start:" >&2
  echo "$STOPPED_REASON" >&2
  exit 1
fi

for CONTAINER_EXIT_CODE in $EXIT_CODE
do
  if [ "$CONTAINER_EXIT_CODE" -ne 0 ]; then
    echo "ECS task ran into an error (exit codes $EXIT_CODE). Please check cloudwatch logs." >&2
    exit 1
  fi
done

echo "ECS task completed successfully."
exit 0
