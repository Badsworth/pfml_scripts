# Script to create an RDS IAM user in the database.
# This only needs to be run whenever a new RDS database is created.
# 
# This relies on resources and outputs created in infra/api, which should
# be updated prior to running this script.
#
set -eo pipefail

DIR=$(dirname "${BASH_SOURCE[0]}")

ENV_NAME=$1

if ! [ -z "$CI" ]; then
    AUTHOR=github-actions
else
    AUTHOR=$2
fi

if [ -z "$ENV_NAME" ] || [ -z "$AUTHOR" ]; then
    echo "Usage: ./rds_user.sh ENV_NAME [AUTHOR]"
    echo "ex: ./rds_user.sh test first_name.last_name"
    exit 1
fi

pushd $DIR/../../infra/api/environments/$ENV_NAME
TF_OUTPUTS=$(terraform output -json)
popd

NETWORK_CONFIG=$(jq \
    --argjson SUBNETS "$(echo $TF_OUTPUTS | jq .subnets.value)" \
    --argjson SECURITY_GROUPS "$(echo $TF_OUTPUTS | jq .security_groups.value)" \
    '.awsvpcConfiguration.subnets=$SUBNETS |
     .awsvpcConfiguration.securityGroups=$SECURITY_GROUPS' \
    $DIR/network_config.json.tpl)

TASK_DEFINITION=$(echo $TF_OUTPUTS | jq .create_rds_user_task_arn.value | cut -d'/' -f2 | sed -e 's/^"//' -e 's/"$//')

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

EXIT_STATUS=$(aws ecs describe-tasks --cluster $ENV_NAME --task $TASK_ARN | jq -r '.tasks[].containers[].exitCode')

if [ $EXIT_STATUS -ne 0 ]
then

  echo "User Creation ran into an error. Please check cloudwatch logs." >&2
  exit 1

else

  echo "User Creation completed successfully."
  exit 0

fi