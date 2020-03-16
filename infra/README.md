Infrastructure
==========

## Introduction

This directory houses the configuration needed for maintaining PFML infrastructure. We use [Terraform](https://terraform.io) to manage our infra in a modular, concise, and reusable fashion.

## Directory Structure

```
└── aws                 🏡 infrastructure for AWS, shared across VPCs e.g. docker image registries.

└── vpc                 🏡 infrastructure for a VPC, shared across applications e.g. an S3 bucket, API Gateway and ECS cluster.
    └── template        🏗  shared template for a VPC
    └── environments
        └── sandbox     ⛱  prototype VPC

└── portal              🏡 infrastructure for a PFML portal environment
    └── config          🚪 environment variables for configuring the Portal
    └── template        🏗  shared template for portal env
    └── environments

└── api                 🏡 infrastructure for a PFML api environment
    └── template        🏗  shared template for api env
    └── environments
```

## tfstate files

Each environment for a component has a `.tfstate` file that is stored in S3 and synchronized using a DynamoDB lock table. Terraform relies on this state file for every command and must acquire the lock in order to use it, so only one person or system can run a terraform command at a time.

```
S3
└── massgov-pfml-global
    └── terraform
        └── aws.tfstate
└── massgov-pfml-sandbox
    └── terraform
        └── vpc.tfstate
        └── terraform.tfstate  # should be portal.tfstate in the future
        └── api.tfstate
```

## Local Setup

These steps are required before running terraform commands locally on your machine.

### Configure AWS

Since we manage AWS resources using Terraform, AWS credentials are needed to run terraform commands. You'll need a `~/.aws/credentials` file with the following stanza:

```yml
[nava-internal]
aws_access_key_id = <access key>
aws_secret_access_key = <secret key>
```

You can retrieve these credentials by going to the [AWS Console](https://console.aws.amazon.com/iam/home?#/security_credentials) and creating a new access key.

You'll also need to set your AWS_PROFILE environment variable to `nava-internal`. This can be added to your `.bashrc`/`.zshrc` or done on a case-by-case basis with:

```
export AWS_PROFILE=nava-internal
```

### Install Terraform

You'll also need terraform 0.12.20+. The best way to manage terraform versions is with [Terraform Version Manager](https://github.com/tfutils/tfenv).

```
$ brew install tfenv
$ tfenv install 0.12.20
```

## Runbook

To view pending changes to infrastructure within an environment directory:

```
$ terraform init
$ terraform plan
```

To apply changes to infrastructure:
```
$ terraform apply
```
