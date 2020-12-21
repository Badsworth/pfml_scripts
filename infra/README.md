# Infrastructure

This directory houses the configuration needed for maintaining PFML infrastructure.
We use [Terraform](https://terraform.io) to manage our infra in a modular, concise, and reusable fashion.

- [Local Setup](#local-setup)
- [Runbook](#runbook)
- [Directory Structure](#directory-structure)
- [tfstate files](#tfstate-files)
- [Troubleshooting](#troubleshooting)

## Local Setup

These steps are required before running terraform or test commands locally on your machine.

<details>
<summary><b>1. Configure AWS</b></summary>
<p>

Since we manage AWS resources using Terraform, AWS credentials are needed to run terraform commands.

#### EOTSS/PFML AWS Account

For the EOTSS-provided PFML account, access to the AWS CLI is federated by Centrify.
To work with this, Centrify has a python CLI tool for logging in and generating AWS access keys.

PFML has a wrapper command around this CLI tool. By default, we install it as `login-aws`, but you can provide your own when prompted.

First, make sure you have some sort of python3 environment.
If not, the easiest way to do this is with [pyenv](https://github.com/pyenv/pyenv) or [asdf](https://asdf-vm.com/#/).

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

Since this pulls down a git repository, it is recommended that the installation location you provide is your general git home, if you have one. In other words, the dir that `pfml/` lives in. For example, if `pfml` lives in `/git`:

```sh
../bin/centrify/install-centrify-aws-cli.sh ~/code/git
```

Once it is installed, you can run the login-aws command to generate a 1-hour AWS access key. You can look up your AWS role (AWS-498823821309-NonPROD-Admins, AWS-498823821309-ViewOnly) through the web interface:

```sh
login-aws
```

<details>
<summary>Example login for Infrastructure-Admin_profile. </summary>
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


If you have multiple roles in AWS, you may encounter a prompt to choose between the roles. This prompt will continue prompting you for a role choice even after you have entered it. It does not exit on its own so you will have to command interrupt (ctrl-c) out of the process. 

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

To view pending changes to infrastructure within an environment directory (i.e. `/test`, `/stage`):

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

In order to send emails from an SES email address, the email must first be verified.
Ensure you have someone who can access the inbox of the email you'll be setting, so they can verify it.

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
└── api                 🏡 infrastructure for a PFML api environment
    └── template        🏗  shared template for api env
    └── environments

└── constants           🏡 infrastructure data shared across all applications and all environments, e.g. a common block of aws tags

└── ecs-tasks           🏡 infrastructure for adhoc PFML API ECS tasks
    └── template        🏗  shared template for API ecs tasks
    └── environments

└── env-shared          🏡 infrastructure for an environment, shared across applications e.g. an API Gateway and ECS cluster.
    └── template        🏗  shared template for an env
    └── environments
        └── test        ⛱  test env, deployed on every merged commit.
        └── stage       ⛱  staging env, deployed on every push to deploy/api/stage
        └── prod        ⛱  production env, deployed on every push to deploy/api/prod

└── pfml-aws            🏡 infrastructure for AWS and VPCs, shared across envs e.g. developer IAM roles,
                           docker registries, and network load balancers for each VPC.

└── pagerduty           🏡 configuration for pagerduty schedules and on-call policies

└── portal              🏡 infrastructure for a PFML portal environment
    └── template        🏗  shared template for portal env
    └── environments

```

## tfstate files

Each environment for a component has a `.tfstate` file that is stored in S3 and synchronized using a DynamoDB lock table.
Terraform relies on this state file for every command and must acquire the lock in order to use it, so only one person or system can run a terraform command at a time.

```
S3
└── massgov-pfml-aws-account-mgmt
    └── terraform
        └── aws.tfstate
        └── pagerduty.tfstate
└── massgov-pfml-test-env-mgmt
    └── terraform
        └── env-shared.tfstate
        └── portal.tfstate
        └── api.tfstate
        └── ecs-tasks.tfstate
```

## Troubleshooting

Sometimes, Terraform does things you might not expect it to do.

### I am unable to login via login-aws

If you are seeing `Error in calling https://eotss.my.centrify.com/Security/StartAuthentication - Please refer logs.` You can find the logs in `centrify-aws-cli-utilities/Python-AWS/centrify-python-aws.log`

In the logs, if you are seeing errors related to the SSL cert, then replace the `cacerts_eotss.pem` file in the same dir with the one below.
<details>
<summary>SSL cert to replace cacerts_eotss.pem </summary>
<p>
    
```
-----BEGIN CERTIFICATE-----
MIIGwTCCBamgAwIBAgIQBZLpXWteAA4fymzo4iR+UDANBgkqhkiG9w0BAQsFADBN
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMScwJQYDVQQDEx5E
aWdpQ2VydCBTSEEyIFNlY3VyZSBTZXJ2ZXIgQ0EwHhcNMTgxMTI4MDAwMDAwWhcN
MjAxMjAyMTIwMDAwWjB9MQswCQYDVQQGEwJVUzETMBEGA1UECBMKQ2FsaWZvcm5p
YTEUMBIGA1UEBxMLU2FudGEgQ2xhcmExFjAUBgNVBAoTDUlkYXB0aXZlLCBMTEMx
DzANBgNVBAsTBkRldk9wczEaMBgGA1UEAwwRKi5teS5pZGFwdGl2ZS5hcHAwggEi
MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDWx9tWOAcSJznyf0NUwmGQJWoo
Eq54Z2Z/8nlRxQk1i7oJmUdzEp+qtoQmkEY5STF6UVolZ/xwPNZN4GDjJ28G2bGh
NyOwG7pmwFkIoKjcHX0VcyDluj7g0pv41gDNIdAZZXgha2RKieesYvaHCWMOlqhy
hkTHa6R3w/QsVImg15wkajyR85VM4/8dpDQDbyyODcGIvS4qfbWppZPiHx+VruLK
Bjnb4zA4x85JcQoky7ZINgc/9n3/LCZX0eJg0Spea5uh7BXiPnRO518GgMrvtjMb
/DLJ8P6c9Y8Q90idzik7bmV72i+Xpb1xLp/eQuA49oN/bPFdtpEM5Ql45WvFAgMB
AAGjggNrMIIDZzAfBgNVHSMEGDAWgBQPgGEcgjFh1S8o541GOLQs4cbZ4jAdBgNV
HQ4EFgQUSYFXmEBesR9bKRXcTmv9SCc1iMMwLQYDVR0RBCYwJIIRKi5teS5pZGFw
dGl2ZS5hcHCCD215LmlkYXB0aXZlLmFwcDAOBgNVHQ8BAf8EBAMCBaAwHQYDVR0l
BBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMGsGA1UdHwRkMGIwL6AtoCuGKWh0dHA6
Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9zc2NhLXNoYTItZzYuY3JsMC+gLaArhilodHRw
Oi8vY3JsNC5kaWdpY2VydC5jb20vc3NjYS1zaGEyLWc2LmNybDBMBgNVHSAERTBD
MDcGCWCGSAGG/WwBATAqMCgGCCsGAQUFBwIBFhxodHRwczovL3d3dy5kaWdpY2Vy
dC5jb20vQ1BTMAgGBmeBDAECAjB8BggrBgEFBQcBAQRwMG4wJAYIKwYBBQUHMAGG
GGh0dHA6Ly9vY3NwLmRpZ2ljZXJ0LmNvbTBGBggrBgEFBQcwAoY6aHR0cDovL2Nh
Y2VydHMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0U0hBMlNlY3VyZVNlcnZlckNBLmNy
dDAMBgNVHRMBAf8EAjAAMIIBfgYKKwYBBAHWeQIEAgSCAW4EggFqAWgAdgCkuQmQ
tBhYFIe7E6LMZ3AKPDWYBPkb37jjd80OyA3cEAAAAWdcMm4uAAAEAwBHMEUCIQCc
tcUuk0iJ3zqb2pi23NIfR1+gqP12Hfhw/rci6jHZAwIgLWMWxoVxYX5BzrvDwFey
EW1yIoQ38Et8yEVC55iiWWUAdgCHdb/nWXz4jEOZX73zbv9WjUdWNv9KtWDBtOr/
XqCDDwAAAWdcMm8JAAAEAwBHMEUCIQDPYgDQvqKIHSmLHX3fy811iJ7vU6Li1zO1
NMn+mTfjKgIgA8JHz/W0XcnHRYUdkboUz6K7Y52wmkgJMtn5Dyxx9+YAdgBvU3as
MfAxGdiZAKRRFf93FRwR2QLBACkGjbIImjfZEwAAAWdcMm+OAAAEAwBHMEUCIQCB
kChV9g+w9kInvvqPmsseDOmdwEE6MfQHoq/e82D/0QIgQc0mXnQHwlk72FlDYuYz
C9JDcggCIB5NMBit9up5Be8wDQYJKoZIhvcNAQELBQADggEBAJ5ytUfKOrx7CK+P
EQJ4Ld3qPYimduylIC1GAIgz9eQ5DEMowZfkhWHYF1reiOYOES4qqKd20LdGrsCb
xSwctz+fqlIR/nQJgynAazPT+Tx2uBJ+LAK09lLrpSAPhE61SQEROsnhDefOKOH2
Z6SI84Fvj9zAcyQ8QEHnDU+FObOVNtvQAdvQP7q+cpeS78TkKbRJYSL9JwsxX70U
LpOPppGZdsqF04ZyrRE2THEKhIvwgDKat54r2XKwXfGy9NGMfDsafbdlQj4ECJOk
9lphbgNmeDJtv7PBJPInEjB0TC+VnOXGYeiw5hR4Tc7lmJEQMQUuogBJIzS933Id
ze3/ZuU=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIElDCCA3ygAwIBAgIQAf2j627KdciIQ4tyS8+8kTANBgkqhkiG9w0BAQsFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBD
QTAeFw0xMzAzMDgxMjAwMDBaFw0yMzAzMDgxMjAwMDBaME0xCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxJzAlBgNVBAMTHkRpZ2lDZXJ0IFNIQTIg
U2VjdXJlIFNlcnZlciBDQTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
ANyuWJBNwcQwFZA1W248ghX1LFy949v/cUP6ZCWA1O4Yok3wZtAKc24RmDYXZK83
nf36QYSvx6+M/hpzTc8zl5CilodTgyu5pnVILR1WN3vaMTIa16yrBvSqXUu3R0bd
KpPDkC55gIDvEwRqFDu1m5K+wgdlTvza/P96rtxcflUxDOg5B6TXvi/TC2rSsd9f
/ld0Uzs1gN2ujkSYs58O09rg1/RrKatEp0tYhG2SS4HD2nOLEpdIkARFdRrdNzGX
kujNVA075ME/OV4uuPNcfhCOhkEAjUVmR7ChZc6gqikJTvOX6+guqw9ypzAO+sf0
/RR3w6RbKFfCs/mC/bdFWJsCAwEAAaOCAVowggFWMBIGA1UdEwEB/wQIMAYBAf8C
AQAwDgYDVR0PAQH/BAQDAgGGMDQGCCsGAQUFBwEBBCgwJjAkBggrBgEFBQcwAYYY
aHR0cDovL29jc3AuZGlnaWNlcnQuY29tMHsGA1UdHwR0MHIwN6A1oDOGMWh0dHA6
Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydEdsb2JhbFJvb3RDQS5jcmwwN6A1
oDOGMWh0dHA6Ly9jcmw0LmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydEdsb2JhbFJvb3RD
QS5jcmwwPQYDVR0gBDYwNDAyBgRVHSAAMCowKAYIKwYBBQUHAgEWHGh0dHBzOi8v
d3d3LmRpZ2ljZXJ0LmNvbS9DUFMwHQYDVR0OBBYEFA+AYRyCMWHVLyjnjUY4tCzh
xtniMB8GA1UdIwQYMBaAFAPeUDVW0Uy7ZvCj4hsbw5eyPdFVMA0GCSqGSIb3DQEB
CwUAA4IBAQAjPt9L0jFCpbZ+QlwaRMxp0Wi0XUvgBCFsS+JtzLHgl4+mUwnNqipl
5TlPHoOlblyYoiQm5vuh7ZPHLgLGTUq/sELfeNqzqPlt/yGFUzZgTHbO7Djc1lGA
8MXW5dRNJ2Srm8c+cftIl7gzbckTB+6WohsYFfZcTEDts8Ls/3HB40f/1LkAtDdC
2iDJ6m6K7hQGrn2iWZiIqBtvLfTyyRRfJs8sjX7tN8Cp1Tm5gr8ZDOo0rwAhaPit
c+LJMto4JQtV05od8GiG7S5BNO98pVAdvzr508EIDObtHopYJeS4d60tbvVS3bR0
j6tJLp07kzQoH3jOlOrHvdPJbRzeXDLz
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIDrzCCApegAwIBAgIQCDvgVpBCRrGhdWrJWZHHSjANBgkqhkiG9w0BAQUFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBD
QTAeFw0wNjExMTAwMDAwMDBaFw0zMTExMTAwMDAwMDBaMGExCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5j
b20xIDAeBgNVBAMTF0RpZ2lDZXJ0IEdsb2JhbCBSb290IENBMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4jvhEXLeqKTTo1eqUKKPC3eQyaKl7hLOllsB
CSDMAZOnTjC3U/dDxGkAV53ijSLdhwZAAIEJzs4bg7/fzTtxRuLWZscFs3YnFo97
nh6Vfe63SKMI2tavegw5BmV/Sl0fvBf4q77uKNd0f3p4mVmFaG5cIzJLv07A6Fpt
43C/dxC//AH2hdmoRBBYMql1GNXRor5H4idq9Joz+EkIYIvUX7Q6hL+hqkpMfT7P
T19sdl6gSzeRntwi5m3OFBqOasv+zbMUZBfHWymeMr/y7vrTC0LUq7dBMtoM1O/4
gdW7jVg/tRvoSSiicNoxBN33shbyTApOB6jtSj1etX+jkMOvJwIDAQABo2MwYTAO
BgNVHQ8BAf8EBAMCAYYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUA95QNVbR
TLtm8KPiGxvDl7I90VUwHwYDVR0jBBgwFoAUA95QNVbRTLtm8KPiGxvDl7I90VUw
DQYJKoZIhvcNAQEFBQADggEBAMucN6pIExIK+t1EnE9SsPTfrgT1eXkIoyQY/Esr
hMAtudXH/vTBH1jLuG2cenTnmCmrEbXjcKChzUyImZOMkXDiqw8cvpOp/2PV5Adg
06O/nVsJ8dWO41P0jmP6P6fbtGbfYmbW0W5BjfIttep3Sp+dWOIrWcBAI+0tKIJF
PnlUkiaY4IBIqDfv8NZ5YBberOgOzW6sRBc4L0na4UU+Krk2U886UAb3LujEV0ls
YSEY1QSteDwsOoBrp+uvFRTp2InBuThs4pFsiv9kuXclVzDAGySj4dzp30d8tbQk
CAUw7C29C79Fv1C5qfPrmAESrciIxpg0X40KPMbp1ZWVbd4=
-----END CERTIFICATE-----
```

</p>
</details>

If you are seeing an error like the following: `Access Denied. Please check.. An error occurred (InvalidIdentityToken) when calling the AssumeRoleWithSAML operation`, move your existing `~/.aws/credentials` file somewhere else (perhaps rename to something like `archived_credentials_yyyymmdd` in the same directory) and run `login-aws` again. This should succeed and create a new `~/.aws/credentials` file.

### I have an unexpected error not related to my change?

If you see something like this message:

```
Error: Network Load Balancers do not support Stickiness
  on ../../template/load_balancer.tf line 19, in resource "aws_lb_target_group" "app":
  19: resource "aws_lb_target_group" "app" {
```

Try "hard resetting" your Terraform state from the environment you're currently deploying from with the following command:
```bash
rm -rf .terraform/ && terraform init
```
