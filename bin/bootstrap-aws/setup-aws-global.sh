#!/usr/bin/env bash
#
# This script sets up a new AWS account managed via terraform.
#
# It creates the following components:
# - A terraform directory/file for managing the AWS account. This will include things like
#   developer + CI IAM permissions and ECR docker repositories.
#
# - An S3 bucket that holds the terraform state. This file is shared between all developers/CI machines,
#   and is required for terraform to know what has been created and what needs to be cleaned up.
#
#   This will not hold _all_ of our terraform state files. Each environment (test, stage, prod) will
#   have their own buckets for managing their own applications and resources.
#
# - A DynamoDB terraform_locks table, which is used to lock the terraform state files described above.
#   Every time a person or CI machine runs terraform, a lock is inserted into the table to prevent
#   anyone from running terraform until they are done.
#
# Please ensure that this script is idempotent and represents the desired final setup of the S3 bucket
# and DynamoDB table. This will guarantee that any accidental runs of this file are non-destructive.
#
set -euo pipefail

BUCKET_NAME=massgov-pfml-aws-account-mgmt
OUTPUT_DIR=infra/pfml-aws

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)

echo "Using account ${ACCOUNT_ID}."
echo
echo "Running this script will do the following:"
echo "- Create or update the S3 bucket \"$BUCKET_NAME\"."
echo "- Create the DynamoDB table \"terraform_locks\" if it does not exist."
echo "- Recreate the file \"$OUTPUT_DIR/main.tf\"."
echo
read -p "Are you sure? " verify

case "$verify" in
  y|Y|yes|Yes ) echo "continuing.";;
  * ) echo "exiting." && exit 1;;
esac

# Create or check S3 bucket.
#
echo
echo "Checking S3 bucket $BUCKET_NAME..."

# This API call is idempotent and does not error if the bucket already exists.
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $AWS_REGION

# Block all public access.
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable versioning for files in the bucket.
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Enable encryption for files in the bucket by default.
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

# Add tags that are required by the EOTSS AWS Config rule.
aws s3api put-bucket-tagging \
    --bucket $BUCKET_NAME \
    --tagging file://$(dirname "$0")/aws-global-s3-tags.json

echo "✅ S3 bucket $BUCKET_NAME was created or updated."
echo

# Create or check DynamoDB table.
#
echo "Checking DynamoDB table terraform_locks..."

set +eo pipefail
dynamodb_output=$(
    aws dynamodb create-table \
        --table-name terraform_locks \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
        --region $AWS_REGION 2>&1)

dynamodb_status=$?
set -eo pipefail

if [[ $dynamodb_status == 0 ]]; then
    echo "✅ DynamoDB table terraform_locks was created."
elif [[ $dynamodb_output =~ "Table already exists" ]]; then
    echo "✅ DynamoDB table terraform_locks already exists."
else
    echo "🛑 DynamoDB creation failed:"
    echo "$dynamodb_output"
    exit $dynamodb_status
fi

echo
echo "Creating terraform module..."

mkdir -p $OUTPUT_DIR

cat <<EOF > $OUTPUT_DIR/main.tf
provider "aws" {
  region = "${AWS_REGION}"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "${BUCKET_NAME}"
    key            = "terraform/aws.tfstate"
    region         = "${AWS_REGION}"
    dynamodb_table = "terraform_locks"
    encrypt        = "true"
  }
}
EOF

echo "✅ Done! Terraform file created at: $OUTPUT_DIR/main.tf"
