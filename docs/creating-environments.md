# Setting up a new environment

Full E2E process (SOP): https://lwd.atlassian.net/wiki/spaces/DD/pages/1549860868/SOP+New+Environment+Build

---

The easiest way to set up resources in a new environment is using the templates in [/bin/bootstrap-env/](../bin/bootstrap-env).

## 1. Initial Setup

1. Update the [infra/constants/outputs.tf](../infra/constants/outputs.tf) file, specifically:
   - environment_tags
   - environment_shorthand
   - smartronix\_environment\_tags

   You do not need to update domains, api_domains, or cert_domains at this time.

   For smartronix\_environment\_tags, reach out to Ron Lovell, Karen Grant, Andy Rodriguez, and Chris Griffith and ask what the new tag should be based on the environment name. They will kick off the Smartronix CAMS infra-monitoring harness for the new environment as well as start any manual DBA steps for the database.
   
   If you need a new EOTSS-approved tag for environment_tags, send an email to <Tim.L.Sharpe@mass.gov> requesting a new tag.

2. The S3 bucket for holding tfstate files must be created first in [infra/pfml-aws/s3.tf](../infra/pfml-aws/s3.tf). Run `terraform apply`. This may require admin permissions.

1. Send a request to EOTSS (Roy Mounier, cc. Chris Griffith) to update the NonProd Admin role to include `arn:aws:s3:::*-pfml-NEW_ENV*` and `arn:aws:s3:::*-pfml-NEW_ENV-*/*` in the S3 permissions. If Roy is out, create a Service Now request.

  - Search for "AWS Role Access Request/Adjustment"
  - Select "Cloud Engineer" if needed by the form.
  - Select "EOLWD Core" for account.
  - Select "No" for "Member of Cloud Operations Team."
  - In the justification, request the following: "Request for the PFML Account (498823821309). The Nonprod-Admin role should allow access to read from new S3 buckets created for the NEW_ENV environment that is being stood up."

1. After that, individual terraform components (`env-shared`, `api`, `ecs-tasks`, or `portal`) may be set up. We'll use this pattern:

   ```
   pfml$ bin/bootstrap-env/bootstrap-env.sh <new-env> <component>
   ```


## 2. Set up the API

### 2.0 Create the API Gateway

1. Generate the terraform environment folder:

   ```
   pfml$ bin/bootstrap-env/bootstrap-env.sh NEW_ENV env-shared
   ```

   The command above creates a new directory: `infra/env-shared/environments/NEW_ENV`
   
1. From the new directory, update variables in `main.tf` and run:

   ```
   terraform init
   ```

1. Create the environment:

     ```sh
     terraform plan
     ```

     ```sh
     terraform apply
     ```
     
### 2.1 Create the API

1. Manually create `/service/pfml-api-dor-import/NEW_ENV/gpg_decryption_key` in Parameter Store. Copy the value from TEST and use a SecureString on the Advanced Tier.

1. Setup the rest of the secrets in Parameter Store by running ./bin/bootstrap-env/copy-parameters.sh NEW_ENV

   <details>
   <summary>Known and accounted for at time of writing:</summary>

   ```
   Copy from stage:
   - /service/pfml-api-comptroller/NEW_ENV/eolwd-moveit-ssh-key
   - /service/pfml-api-comptroller/NEW_ENV/eolwd-moveit-ssh-key-password
   - /service/pfml-api-dor-import/NEW_ENV/gpg_decryption_key_passphrase
   - /service/pfml-api/NEW_ENV/ctr-data-mart-password
   - /service/pfml-api/NEW_ENV/rmv_client_certificate_password
   - /service/pfml-api/NEW_ENV/service_now_username
   - /service/pfml-api/NEW_ENV/service_now_password

   Manually generate a string and pop it in there:
   - /service/pfml-api/NEW_ENV/dashboard_password
   - /service/pfml-api/NEW_ENV/db-nessus-password

   Generated automaticallly in terraform (no action needed):
   - /service/pfml-api/NEW_ENV/db-password

   Copy from `Cognito AWS Console > app clients` after Portal/Cognito is created:
   - /service/pfml-api/NEW_ENV/cognito_fineos_app_client_id
   - /service/pfml-api/NEW_ENV/cognito_internal_fineos_role_app_client_id
   - /service/pfml-api/NEW_ENV/cognito_internal_fineos_role_app_client_secret
   
   Received from FINEOS (more details below):
   - /service/pfml-api/NEW_ENV/fineos_oauth2_client_secret
   ```
   </details>

1. Add the new environment to `api/newrelic.ini` to set up New Relic APM:

   ```toml
   [newrelic:NEW_ENV]
   app_name = PFML-API-NEW_ENV
   monitor_mode = true
   ```

1. Generate the terraform environment folder: 

   ```
   pfml$ bin/bootstrap-env/bootstrap-env.sh NEW_ENV api
   ```

   The command above creates a new directory: `infra/api/environments/NEW_ENV`
   
1. From the new directory, update variables in `main.tf`, namely:

   - nlb\_port: same port as specified in the API gateway.
   - cors\_origins: set this to be the execute-api URL from API gateway for now. [API\_GATEWAY\_URL]
   - rmv\_client\_certificate\_arn: Retrieve the secretsmanager ARN from AWS secrets manager or from the copy-parameters script output.

3. Run:

   ```
   terraform init
   ```

1. Create the environment, providing an initial application version to deploy. Since this requires a version that is built and pushed to ECR, it's easiest to use the latest version that was [deployed in TEST](https://github.com/EOLWD/pfml/deployments/activity_log?environment=API+%28test%29). This is a Docker image tag that is equivalent to a commit hash.

     ```sh
     $ terraform apply \
     -var='service_docker_tag=82043ae1e04621251fb9e7896176b38c884f027e'
     ```
     
Note that the API will not be working until database migrations are run.

### 2.2 Create the ECS Tasks

1. Generate the terraform environment folder: 

   ```
   pfml$ bin/bootstrap-env/bootstrap-env.sh NEW_ENV ecs-tasks
   ```

   The command above creates a new directory: `infra/ecs-tasks/environments/NEW_ENV`
   
1. Create a PR and run a deployment of this branch to the new environment. See [./deployment.md](deployment.md). This should automatically:

   - Initialize and apply the ECS tasks terraform.
   - Run database migrations.
   - Create the required database users for FINEOS and Smartronix Nessus scans. 

## 3. Setting up the Portal Environment

1. Generate the terraform environment folder:

   ```
   pfml$ bin/bootstrap-env/bootstrap-env.sh NEW_ENV portal
   ```

   The command above creates a new directory: `infra/portal/environments/NEW_ENV `
1. From the new directory, run:

   ```
   terraform init
   ```

1. Create the environment, providing a specific `cloudfront_origin_path` since nothing will be deployed yet. You can use a blank path for now:

     ```sh
     terraform plan -var='cloudfront_origin_path='
     ```

     ```sh
     terraform apply -var='cloudfront_origin_path='
     ```
     
1. Sync the cognito secrets to parameter store: 

   ```sh
   bin/bootstrap-env/sync-cognito-variables.sh $NEW_ENV
   ```

1. Update infra/api/environments/NEW_ENV/main.tf and infra/ecs-tasks/environments/NEW_ENV/main.tf to include the cognito variables as output from the previous script.

   ```
   cognito_user_pool_arn = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/$pool_id"
   cognito_user_pool_id = "$pool_id"
   cognito_user_pool_client_id = "$api_client_id"
   cognito_user_pool_keys_url = "https://cognito-idp.us-east-1.amazonaws.com/$pool_id/.well-known/jwks.json"
   ```

1. Follow [additional steps for new Portal environments](portal/creating-environments.md).

### Configuring Cognito

**This is only required for environments that will not run E2E tests. For most environments this is not required.**

In production, we block high-risk login attempts. This can also be configured for other environments if desired. High-risk login attempts aren't blocked in environments used for testing so that automated test scripts don't get blocked.

Our Terraform scripts enable Advanced Security. however at the time of writing, [Terraform didn't support more granular configuration of the Advanced Security settings](https://github.com/hashicorp/terraform-provider-aws/issues/7007), so there are some manual steps needed:

1. Log into the AWS Console and navigate to the Cognito User Pool for this environment.
1. Click "Advanced Security" in the sidebar
1. [Configure the adaptive authentication behavior](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security.html#cognito-user-pool-configure-advanced-security).
1. On the same page in AWS customize the email notification messages by copy-and-pasting the HTML email templates from [`infra/portal/templates/emails`](../infra/portal/templates/emails/).
1. Ensure the email FROM address is `"NEWENV-SHORTHAND_Department of Family and Medical Leave" \<PFML_DoNotReply@eol.mass.gov\>"`.

## 4. Integrating with FINEOS

### Configure PFML credentials for FINEOS

1. Create the FINEOS user the in PFML database.

   ```sh
   ./bin/run-ecs-task/run-task.sh NEW_ENV db-create-fineos-user FIRST_NAME.LAST_NAME
   ```
   
1. Create a file locally with the Cognito FINEOS app client ID and secret. You can view this data by going to AWS Console > AWS Cognito > User Pools > [[ select the environment's user pool ]] > App Clients. Look for the `fineos-pfml-{env}` client.
1. Send it to FINEOS over interchange, then delete the file from your local computer. Also send the following details:

  - Auth URL: (e.g. https://paidleave-api-cps-preview.eol.mass.gov/api/v1/oauth2/token)
  - Integration URLs (e.g. https://paidleave-api-cps-preview.eol.mass.gov/api/v1/rmv-check, https://paidleave-api-cps-preview.eol.mass.gov/api/v1/financial-eligibility)
  - VPC IP Address (Should be nonprod IP: VPC-EOLWD-PFML-NonProd, vpc-097793bd468be1c65, 10.203.224.0/22)
  - VPC ID (Should be nonprod IP: VPC-EOLWD-PFML-NonProd, vpc-097793bd468be1c65, 10.203.224.0/22)
  - VPC S3 Endpoint ID (Should be nonprod endpoint: vpce-057c4dd758ba5ccb1)

### Configure FINEOS credentials for PFML

1. FINEOS should send a file to us with an oauth client ID and secret. If not, ping Howard Teasley and Darnel.
1. The client ID should be configured in **both**:
   - infra/api/environments/NEW\_ENV/main.tf and 
   - infra/ecs-tasks/environments/NEW\_ENV/main.tf.
1. The client secret value should be updated in parameter store (`/service/pfml-api/NEW_ENV/fineos_oauth2_client_secret`).

Verify the following details with FINEOS:
- Will SSO be enabled? (If so, we need to configure the FINEOS user as OASIS instead of CONTENT)
- What is the FINEOS URL?
- What is the FINEOS S3 path for data exports/imports?

## 4. Update CI and Monitoring

1. Add the new environment to the [CI build matrix](/.github/workflows/infra-validate.yml) so it can be validated when it's changed.
1. Add the environment to the [monitoring module](/infra/monitoring/alarms.tf) to create API and Portal alarms that are linked to PagerDuty.


## Setting up Custom Domains

If we expect FINEOS to call the PFML API, you'll need a custom mass.gov domain for the environment. Please f	ollow these steps:

1. Request an ACM cert in the AWS Console > AWS Certificate Manager, with Email Verification. Example:

   |Domain Name|SANs|
   |---|---|
   |paidleave-performance.eol.mass.gov|paidleave-training.eol.mass.gov,<br>paidleave-api-training.eol.mass.gov,<br>paidleave-api-performance.eol.mass.gov|

2. Send an email to Vijay with the domain name/SANs, so he can request approval from Sarah Bourne / Chris Velluto / Bill Cole. Boilerplate:

   ```
   To: Rajagopalan, Vijay (DFML) <Vijay.Rajagopalan2@mass.gov>; 
       Griffith, Christopher (EOL) <Christopher.Griffith@detma.org>;
       Bourne, Sarah (EOTSS) <sarah.bourne@mass.gov>; 
       Velluto, Christopher (EOTSS) <christopher.velluto@mass.gov>; 
       Cole, William (EOTSS) <william.cole@mass.gov>
       
   cc: Yeh, Kevin (DFML) <Kevin.Yeh@mass.gov>
        
   Hi all,

   We’re setting up the PFML API and Portal breakfix and cps-preview environments to interface with new FINEOS environments.

   I’ll be requesting an ACM certificate shortly. The certificate request will be as outlined below:

   domain_name: paidleave-ENV.eol.mass.gov
   SANs: paidleave-api-ENV.eol.mass.gov, paidleave-OTHER_ENV.eol.mass.gov, paidleave-api-OTHER_ENV.eol.mass.gov

   @Rajagopalan, Vijay (DFML) @Griffth, Chris (EOL) can you confirm this request from the PFML end?

   Thanks.
   ```

3. Once EOTSS has approved the certificate, update the domains, api_domains, and cert_domains map in the following file:

   * [infra/constants/outputs.tf](/infra/constants/outputs.tf)

4. After merging and applying the changes, create a ServiceNow request for CNAME entries for the Portal and Gateway. 

   These should all be cloudfront URLs. Check the AWS Console under API Gateway > Custom Domain Names for the API Gateway Cloudfront URLs.

   | App             | CNAME                              | URL                            |
   | --------------- | ---------------------------------- | ------------------------------ |
   | API perf        | paidleave-api-performance.eol.mass.gov | https://abcd123.cloudfront.net |
   | API training    | paidleave-api-training.eol.mass.gov    | https://zaww123.cloudfront.net |
   | Portal perf     | paidleave-performance.eol.mass.gov     | https://vfcs123.cloudfront.net |
   | Portal training | paidleave-training.eol.mass.gov        | https://qwer123.cloudfront.net |
   
   Visit https://massgov.service-now.com/sp and search for DNS (Domain Name System). Create one ticket per record.
   
   Fill details in as follows (example):
   
   <img width="400" alt="Screen Shot 2021-04-15 at 1 24 54 PM" src="https://user-images.githubusercontent.com/2308368/114912713-53e18d00-9dee-11eb-9561-30034d00090d.png">

   Example Description:
   
   ```
   Please create a new CName entry to point paidleave-api-breakfix.eol.mass.gov to djoikhjp9s25o.cloudfront.net.

   Point of Contacts for more info: 
   Rajagopalan, Vijay (DFML) <Vijay.Rajagopalan2@mass.gov> 
   Griffith, Christopher (EOL) <Christopher.Griffith@detma.org>
   ```

5. After they create the CNAME entries, the custom domains should direct to the appropriate applications.




