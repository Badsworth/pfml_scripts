# First-time Setup

If you're working with the `infra` directory, these steps are required before running terraform or test commands locally on your machine.

## 1. Configure AWS

Since we manage AWS resources using Terraform, AWS credentials are needed to run terraform commands. Access to the AWS CLI is federated by AWS SSO, backed by Azure AD.

### Using AWS CLI:

If you've already configured AWS SSO in your CLI, run `aws sso login`.

### Configuring AWS SSO
For first-time setup, run `aws configure sso` using the following config:

* URL: https://coma.awsapps.com/start
* Region: us-east-1

It will open up a browser to complete sign-in. Log in using your Azure AD credentials. It will eventually direct you to close your browser.

In your terminal, select a role and use defaults for the rest of the values.

It will show a message like this:

```
To use this profile, specify the profile name using --profile, as shown:

aws s3 ls --profile eolwd-pfml-infrastructure-admin-498823821309
```

You can set the profile for all future commands using `export AWS_PROFILE=eolwd-pfml-infrastructure-admin-498823821309`.

### Using the Browser

Visit [https://coma.awsapps.com/start](https://coma.awsapps.com/start) and log in with your Azure AD credentials. The UI will provide CLI credentials via `export` commands that you can paste into your terminal.

## 2. Install Terraform

Refer to the root-level [README](../README.md) for instructions on installing terraform.

## 3. Optionally install NPM dependencies

To locally run tests for JS lambdas, you'll also need to run the following with `infra/` as the working directory:

```
npm install
```
