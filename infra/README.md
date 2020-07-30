# Infrastructure

This directory houses the configuration needed for maintaining PFML infrastructure. We use [Terraform](https://terraform.io) to manage our infra in a modular, concise, and reusable fashion.

- [Local Setup](#local-setup)
- [Runbook](#runbook)
- [Directory Structure](#directory-structure)
- [tfstate files](#tfstate-files)

## Local Setup

These steps are required before running terraform or test commands locally on your machine.

<details>
<summary><b>1. Configure AWS</b></summary>
<p>

Since we manage AWS resources using Terraform, AWS credentials are needed to run terraform commands.

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
```

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

### Setting up a new environment

🔗 See [docs/creating-environments.md](../docs/creating-environments.md) to learn how to create a new environment.

### Adding a new SES email address

In order to send emails from an SES email address, the email must first be verified. Ensure you have someone who can access the inbox of the email you'll be setting so they can verify it.

#### Creating the email in Terraform

1. Run `terraform apply`, which will likely return an error indicating you need to verify the email address.
1. Verify the email address by clicking the link in the verification email that should have been sent after the previous step.
1. Run `terraform apply` again, which should be successful this time

#### Creating the email in AWS Console

Alternatively, you can create the email in the AWS Console and verify it:

1. Add the email to SES through the AWS Console
1. Verify the email address by clicking the link in the verification email that should have been sent after the previous step.
1. Import the SES email resource:
    ```
    terraform import aws_ses_email_identity.example email@example.com
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

### Testing Github Actions permissions

Since Github Actions has different permissions than developers and admins, it's useful to test terraform configs using our CI/CD role so we know
that they can be run on Github Actions with the right read/write permissions. This is recommended if you're adding a new service into our ecosystem.

1. Ensure you have the AWS CLI:

   ```
   pip install awscli
   ```

2. Generate a session:

   ```
   aws sts assume-role --role-arn arn:aws:iam::498823821309:role/ci-run-deploys --role-session-name <any-session-name>
   ```

3. Copy the access key, secret, and session token into your ~/.aws/credentials under a new profile so it looks like this:

   ```
   [ci-run-deploys]
   aws_access_key_id = 123
   aws_secret_access_key = 456
   aws_session_token = 789
   ```

4. Use the profile:

   ```
   export AWS_PROFILE=ci-run-deploys
   ```

5. Run terraform as usual.

## Directory Structure

```
└── aws                 🏡 infrastructure for AWS and VPCs, shared across envs e.g. developer IAM roles,
                           docker registries, and network load balancers for each VPC.

└── env-shared          🏡 infrastructure for an environment, shared across applications e.g. an API Gateway and ECS cluster.
    └── template        🏗  shared template for an env
    └── environments
        └── test        ⛱  test env, deployed on every merged commit.
        └── stage       ⛱  staging env, deployed on every push to deploy/api/stage
        └── prod        ⛱  production env, deployed on every push to deploy/api/prod

└── portal              🏡 infrastructure for a PFML portal environment
    └── template        🏗  shared template for portal env
    └── environments

└── api                 🏡 infrastructure for a PFML api environment
    └── template        🏗  shared template for api env
    └── environments

└── ecs-tasks           🏡 infrastructure for adhoc PFML API ECS tasks
    └── template        🏗  shared template for API ecs tasks
    └── environments

```

## tfstate files

Each environment for a component has a `.tfstate` file that is stored in S3 and synchronized using a DynamoDB lock table. Terraform relies on this state file for every command and must acquire the lock in order to use it, so only one person or system can run a terraform command at a time.

```
S3
└── massgov-pfml-aws-account-mgmt
    └── terraform
        └── aws.tfstate
└── massgov-pfml-test-env-mgmt
    └── terraform
        └── env-shared.tfstate
        └── portal.tfstate
        └── api.tfstate
        └── ecs-tasks.tfstate
```
