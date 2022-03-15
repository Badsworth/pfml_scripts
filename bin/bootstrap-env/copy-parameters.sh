#!/usr/bin/env bash
#
# Utility script for setting up parameter store values for new environments.
# You should be a prod admin to run the script in production environment
# Creates 15 parameters
#

set -euo pipefail

USAGE=$(cat <<-EOF
Utility script for setting up parameter store values for new environments.

Usage: copy-parameters.sh [--source COPY_FROM_ENV] NEW_ENV

  e.g. copy-parameters.sh breakfix
  e.g. copy-parameters.sh --source test breakfix
EOF
)

# Verify that the usage looks roughly correct.
if [ "$#" -ne 1 ] && [ "$#" -ne 3 ]; then
    echo "$USAGE"
    exit 1
fi

# Default to copying from stage.
COPY_FROM_ENV=stage

# Read arguments
for arg in "$@"; do
  shift
  case "$arg" in
      "--source") COPY_FROM_ENV=$1 && shift ;;
      *) NEW_ENV=$arg
  esac
done

# Verify arguments were parsed reasonably
if [ -z "$NEW_ENV" ] || [ -z "$COPY_FROM_ENV" ]; then
    echo "$USAGE"
    exit 1
fi

# Verify the values with the user before proceeding.
read -p "Copying values from $COPY_FROM_ENV to $NEW_ENV. Continue? (y/n) " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "exiting."
    exit 1
fi

# Copy parameters wholesale from stage to connect to various staging services.
parameters=$(aws ssm get-parameters --with-decryption --names \
    "/service/pfml-api-comptroller/$COPY_FROM_ENV/eolwd-moveit-ssh-key" \
    "/service/pfml-api-comptroller/$COPY_FROM_ENV/eolwd-moveit-ssh-key-password" \
    "/service/pfml-api-dor-import/$COPY_FROM_ENV/gpg_decryption_key_passphrase" \
    "/service/pfml-api/$COPY_FROM_ENV/ctr-data-mart-password" \
    "/service/pfml-api/$COPY_FROM_ENV/rmv_client_certificate_password" \
    "/service/pfml-api/$COPY_FROM_ENV/service_now_username" \
    "/service/pfml-api/$COPY_FROM_ENV/service_now_password" | jq '.Parameters' | jq -c '.[]')

while IFS= read -r row; do
    name=$(printf "%s" "$row" | jq -r '.Name')
    value=$(printf "%s" "$row" | jq -r '.Value')
    type=$(printf "%s" "$row" | jq -r '.Type')

    new_name=$(echo $name | sed "s/$COPY_FROM_ENV/$NEW_ENV/g")

    echo "Creating $new_name from $name ($type)"
    set +e
    aws ssm put-parameter \
        --name $new_name \
        --value "$value" \
        --type $type \
        --tags Key=environment,Value=$NEW_ENV \
    || \
    echo "Parameter already exists!"
    set -e
done <<< "$parameters"

# Generate random values for these parameters and insert them into parameter store.
#
# Nessus password: 32 random alphanumeric characters
# ImportLog dashboard password: 16 random alphanumeric characters
set +o pipefail
DB_NESSUS_PASS=$(< /dev/urandom LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
DASHBOARD_PASS=$(< /dev/urandom LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
set -euo pipefail
echo "Creating /service/pfml-api/$NEW_ENV/dashboard_password"

set +e
aws ssm put-parameter \
    --name "/service/pfml-api/$NEW_ENV/dashboard_password" \
    --value "$DASHBOARD_PASS" \
    --type "SecureString" \
    --tags Key=environment,Value=$NEW_ENV \
    || \
    echo "Parameter already exists!"

echo "Creating /service/pfml-api/$NEW_ENV/db-nessus-password"

aws ssm put-parameter \
    --name "/service/pfml-api/$NEW_ENV/db-nessus-password" \
    --value "$DB_NESSUS_PASS" \
    --type "SecureString" \
    --tags Key=environment,Value=$NEW_ENV \
    || \
    echo "Parameter already exists!"

echo "done"
set -e

# Add placeholders for values that we need to spin up the API/ECS tasks.
# These can be filled out in later steps of the environment creation process.
placeholders=(
    "/service/pfml-api/$NEW_ENV/fineos_oauth2_client_secret"
    "/service/pfml-api/$NEW_ENV/cognito_fineos_app_client_id"
    "/service/pfml-api/$NEW_ENV/cognito_internal_fineos_role_app_client_id"
    "/service/pfml-api/$NEW_ENV/servicenow_oauth2_client_secret"
    "/service/pfml-api/$NEW_ENV/cognito_servicenow_app_client_id"
    "/service/pfml-api/$NEW_ENV/cognito_internal_servicenow_role_app_client_id"
)

set +e
for placeholder in ${placeholders[*]}; do
    echo "Creating placeholder for $placeholder"

    aws ssm put-parameter \
        --name "$placeholder" \
        --value "TODO" \
        --type "SecureString" \
        --tags Key=environment,Value=$NEW_ENV \
    || \
    echo "Parameter already exists!"

done
set -e

# Copy the binary RMV client certificate in Secrets Manager.
# This is used to authenticate with the stage RMV API.
echo "Copying RMV client certificate from $COPY_FROM_ENV"

rm -f .rmv-cert

aws secretsmanager get-secret-value \
    --secret-id "/service/pfml-api-$COPY_FROM_ENV/rmv_client_certificate" \
    | jq -r ".SecretBinary" | base64 --decode >> .rmv-cert

# Create when none exist or update when exists
set +e
aws secretsmanager create-secret \
    --name "/service/pfml-api-$NEW_ENV/rmv_client_certificate" \
    --secret-binary fileb://.rmv-cert \
    || \
    echo "Client certificate already exists!"

rm .rmv-cert

echo "done"
