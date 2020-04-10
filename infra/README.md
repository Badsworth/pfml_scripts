Infrastructure
==========

This directory houses the configuration needed for maintaining PFML infrastructure. We use [Terraform](https://terraform.io) to manage our infra in a modular, concise, and reusable fashion.

* [Local Setup](#local-setup)
* [Runbook](#runbook)
* [Directory Structure](#directory-structure)
* [tfstate files](#tfstate-files)

## Local Setup

These steps are required before running terraform or test commands locally on your machine.

<details>
<summary><b>1. Configure AWS</b></summary>
<p>

Since we manage AWS resources using Terraform, AWS credentials are needed to run terraform commands. 

#### Nava Sandbox

For the Nava AWS sandbox, you'll need a `~/.aws/credentials` file with the following stanza:

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

#### EOTSS/PFML AWS Account

For the EOTSS-provided PFML account, access to the AWS CLI is federated by Centrify. To work with this, Centrify has a python CLI tool for logging in and generating AWS access keys.

PFML has a wrapper command around this CLI tool. By default, we install it as `login-aws`, but you can provide your own when prompted.

First, make sure you have some sort of python3 environment. If not, the easiest way to do this is with [pyenv](https://github.com/pyenv/pyenv) or [asdf](https://asdf-vm.com/#/).

```
# For OSX
brew install pyenv
echo 'eval "$(pyenv init -)"' >> ~/.bash_profile (or .zshrc, etc.)
source ~/.bash_profile
pyenv install 3.8.2
```

Install the required libraries:

```
pip install requests boto3 colorama
```

Then install PFML's CLI wrapper with the following script:

```sh
../bin/centrify/install-centrify-aws-cli.sh INSTALL_LOCATION
```

Since this pulls down a git repository, it is recommended that the installation location you provide is your general git home, if you have one. For example:

```sh
../bin/centrify/install-centrify-aws-cli.sh ~/code/git
````

Once it is installed, you can run the login-aws command to generate a 1-hour AWS access key:

```sh
login-aws
```

<details>
<summary>Example login:</summary>
<p>

```
Logfile - centrify-python-aws.log
Please enter your username : kevin.yeh
Password :
OATH OTP Client :
Select the aws app to login. Type 'quit' or 'q' to exit
1 : EOLWD - PFML | aad65420-6a79-412a-9aa1-587c1091d194
Calling app with key : aad65420-6a79-412a-9aa1-587c1091d194
--------------------------------------------------------------------------------

Select a role to login. Choose one role at a time. This
selection might be displayed multiple times to facilitate
multiple profile creations.
Type 'q' to exit.

Please choose the role you would like to assume -
1: arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer
Selecting above role.
You Chose :  arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer
Your SAML Provider :  arn:aws:iam::498823821309:saml-provider/Centrify
home = /Users/kyeah
Display Name : EOLWD - PFML

--------------------------------------------------------------------------------
Your profile is created. It will expire at 2020-04-03 15:30:35+00:00
Use --profile AWS-498823821309-Infrastructure-Admin_profile for the commands
Example -
aws s3 ls --profile AWS-498823821309-Infrastructure-Admin_profile
--------------------------------------------------------------------------------

AWS_PROFILE is currently: default. Run the following command to set it:
export AWS_PROFILE=AWS-498823821309-Infrastructure-Admin_profile
```

</p>
</details>

For convenience, it is recommended that you export AWS_PROFILE or set an alias 
in your startup script to easily set/select the profile in any shell.

```sh
#.zshrc
export AWS_PROFILE=AWS-498823821309-Infrastructure-Admin_profile
```

or

```sh
alias aws-eotss="export AWS_PROFILE=AWS-498823821309-Infrastructure-Admin_profile"
```

Note that this role will be different for full-access roles, e.g.

```sh
export AWS_PROFILE=AWS-498823821309-CloudOps-Engineer_profile
```

</p>
</details>

<details>
<summary><b>2. Install Terraform</b></summary>
<p>

Refer to the root-level [README](../README.md) for instructions on installing terraform.

</p>
</details>

<details>
<summary><b>3. Optionally install NPM dependencies</b></summary>
<p>

To locally run tests, you'll also need to run the following with `infra/` as the working directory:

```
npm install
```

</p>
</details>

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

### Tests

To run the [test suite](../docs/tests.md):

```
npm test
```

Update _all_ [Jest snapshots](../docs/tests.md#Snapshot%20tests), accepting any updates as expected changes:

```
npm run test:update-snapshot
```

Run the project's test suite in watch mode:

```
npm run test:watch
```

> By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.

## Directory Structure

```
└── aws                 🏡 infrastructure for AWS, shared across envs e.g. developer IAM roles and docker image registries.

└── env-shared          🏡 infrastructure for an env, shared across applications e.g. an API Gateway and ECS cluster.
    └── template        🏗  shared template for an env
    └── environments
        └── sandbox     ⛱  prototype env

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
        └── vpc.tfstate        # will be env-shared.tfstate in the PFML AWS account
        └── terraform.tfstate  # will be portal.tfstate in the PFML AWS account
        └── api.tfstate
```
