# Script to run migrations within an environment through an ECS task.
#
# This relies on resources and outputs created in infra/api, which should
# be updated prior to running this script.
#
set -eo pipefail

DIR=$(dirname "${BASH_SOURCE[0]}")

ENV_NAME=$1
TASK_NAME=$2

if ! [ -z "$CI" ]; then
    AUTHOR=github-actions
else
    AUTHOR=$3
fi

if [ -z "$ENV_NAME" ] || [ -z "$TASK_NAME" ] || [ -z "$AUTHOR" ]; then
    echo "Usage: ./run-task.sh ENV_NAME TASK_NAME [AUTHOR]"
    echo "ex: ./run-task.sh test db-migrate-up first_name.last_name"
    exit 1
fi

pushd $DIR/../../infra/ecs-tasks/environments/$ENV_NAME
TF_OUTPUTS=$(terraform output -json || (terraform init && terraform output -json))
popd

NETWORK_CONFIG=$(jq \
    --argjson SUBNETS "$(echo $TF_OUTPUTS | jq .subnets.value)" \
    --argjson SECURITY_GROUPS "$(echo $TF_OUTPUTS | jq .security_groups.value)" \
    '.awsvpcConfiguration.subnets=$SUBNETS |
     .awsvpcConfiguration.securityGroups=$SECURITY_GROUPS' \
    $DIR/network_config.json.tpl)

TASK_DEFINITION=$(echo $TF_OUTPUTS | jq ".ecs_task_arns.value.\"pfml-api-$TASK_NAME\"" | cut -d'/' -f2 | sed -e 's/^"//' -e 's/"$//')

echo "Running $TASK_DEFINITION..."

# Start the ECS task
RUN_TASK=$(aws --region=us-east-1 \
    ecs run-task \
    --cluster $ENV_NAME \
    --started-by "$AUTHOR" \
    --task-definition "$TASK_DEFINITION" \
    --launch-type "FARGATE" \
    --network-configuration "$(echo $NETWORK_CONFIG)")

echo "Started task:"
echo $RUN_TASK | jq .

TASK_ARN=$(echo $RUN_TASK | jq '.tasks[0].taskArn' | sed -e 's/^"//' -e 's/"$//')

aws ecs wait tasks-stopped --region us-east-1 --cluster $ENV_NAME --tasks $TASK_ARN

TASK_STATUS=$(aws ecs describe-tasks --cluster $ENV_NAME --task $TASK_ARN | jq -r '.tasks[]')
EXIT_CODE=$(echo $TASK_STATUS | jq '.containers[].exitCode')

if [ $EXIT_CODE == "null" ]; then
  STOPPED_REASON=$(echo $TASK_STATUS | jq '.stoppedReason')
  echo "ECS task failed to start:" >&2
  echo "$STOPPED_REASON" >&2
  exit 1

elif [ $EXIT_CODE -ne 0 ]; then
  echo "ECS task ran into an error. Please check cloudwatch logs." >&2
  exit 1

else
  echo "ECS task completed successfully."
  exit 0
fi
