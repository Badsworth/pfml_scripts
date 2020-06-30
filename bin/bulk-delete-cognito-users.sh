#!/usr/bin/env bash
USAGE="
Usage: Deletes users in a Cognito user pool that were created before a certain date. This doesn't
handle AWS CLI pagination, so you may need to run this multiple times to delete all the users

args:
COGNITO_USER_POOL_ID - Cognito User Pool ID
CREATE_DATE - (YYYY-MM-DD) Users created before this date will be deleted

example:
./bulk-delete-cognito-users.sh us-east-1_Abcdef 2020-06-01
"

if [[ $# != 2 ]]; then
    echo "$USAGE"
    exit 1
fi

COGNITO_USER_POOL_ID=$1
CREATE_DATE=$2

getUsers() {
  aws cognito-idp list-users --user-pool-id $COGNITO_USER_POOL_ID --output json --query "Users[?UserCreateDate < '$CREATE_DATE'].Username" | jq -r '.[]'
}

echo "! DRY RUN !"
echo "Will delete following users from pool $COGNITO_USER_POOL_ID";
echo ""
getUsers
echo ""

read -p "Are you sure you want to delete these users? (y/n) " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi

echo ""

getUsers | while read uname; do
  echo "Deleting $uname from pool $COGNITO_USER_POOL_ID";
  aws cognito-idp admin-delete-user --user-pool-id $COGNITO_USER_POOL_ID --username $uname;
done