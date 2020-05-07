# Script to run migrations within an environment through an ECS task.
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
    echo "Usage: ./migrate.sh ENV_NAME [AUTHOR]"
    echo "ex: ./migrate.sh test kevin.yeh"
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

TASK_DEFINITION=$(echo $TF_OUTPUTS | jq .migrate_up_task_arn.value | cut -d'/' -f2 | sed -e 's/^"//' -e 's/"$//')

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
