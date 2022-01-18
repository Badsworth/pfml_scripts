ENV=$1
PARAMETER=/service/pfml-api/$ENV/fineos_oauth2_client_secret
REGION=us-east-1

secret=$(aws ssm get-parameter --with-decryption --name $PARAMETER --region $REGION | jq -r '.Parameter.Value')
echo FINEOS_CLIENT_OAUTH2_CLIENT_SECRET=$secret >> test.txt
