# Script for looking up Cognito IDs/secrets and syncing the values to parameter store.
# This also outputs the values needed in infra/api/environments/*/main.tf so you can copy-pasta.
#
# This should be run after the Cognito instance is created through the Portal infra.
#
ENV=$1

if [ -z "$ENV" ]; then
    "Usage: ./sync-cognito-secrets.sh ENV"
fi

echo "Looking up cognito data for the $ENV environment..."

# Cognito User Pool ID
pool_id=$(
    aws cognito-idp list-user-pools --max-results=20 \
        | jq -r ".UserPools | .[] | select(.Name == \"massgov-pfml-$ENV\") | .Id")

# API client that is used for end-user (claimant and leave admin) signup, login, etc.
# We need to set this so end-users are authenticated against this client.
api_client_id=$(
    aws cognito-idp list-user-pool-clients --user-pool-id=$pool_id \
        | jq -r ".UserPoolClients | .[] | select(.ClientName == \"massgov-pfml-$ENV\") | .ClientId")

# FINEOS oauth client that they use to communicate to the PFML API.
#
# We need to set this in parameter store so we can generate a database user for them
# during the create-fineos-user ECS task. This allows them to authenticate and call the
# relevant endpoints, like rmv_check and financial eligibility.
fineos_client_id=$(
    aws cognito-idp list-user-pool-clients --user-pool-id=$pool_id \
        | jq -r ".UserPoolClients | .[] | select(.ClientName == \"fineos-pfml-$ENV\") | .ClientId")

# Internal oauth client used for manual and E2E testing against the endpoints that FINEOS calls,
# such as rmv_check and financial eligibility.
#
# This is set the ID and secret in parameter store so that E2E testing can pull it down during tests. The ID is also used to generate a database user during the create-fineos-user ECS task.
internal_client_id=$(
    aws cognito-idp list-user-pool-clients --user-pool-id=$pool_id \
        | jq -r ".UserPoolClients | .[] | select(.ClientName == \"internal-fineos-role-oauth-pfml-$ENV\") | .ClientId")

internal_secret=$(aws cognito-idp describe-user-pool-client --user-pool-id=$pool_id --client-id=$internal_client_id | jq -r ".UserPoolClient.ClientSecret")

cat <<-EOF
cognito_user_pool_arn = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/$pool_id"
cognito_user_pool_id = "$pool_id"
cognito_user_pool_client_id = "$api_client_id"
cognito_user_pool_keys_url = "https://cognito-idp.us-east-1.amazonaws.com/$pool_id/.well-known/jwks.json"
EOF

echo "Uploading secrets to parameter store..."

aws ssm put-parameter --name "/service/pfml-api/$ENV/cognito_fineos_app_client_id" --value "$fineos_client_id" --type "SecureString" --overwrite
aws ssm put-parameter --name "/service/pfml-api/$ENV/cognito_internal_fineos_role_app_client_id" --value "$internal_client_id" --type "SecureString" --overwrite
aws ssm put-parameter --name "/service/pfml-api/$ENV/cognito_internal_fineos_role_app_client_secret" --value "$internal_secret" --type "SecureString" --overwrite

echo "Done!"
