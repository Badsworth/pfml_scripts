# Test Fineos server from local setup

This documentation shows how you can configure your local set up to interact with the FINEOS server of your choice. 

- [Test Fineos server from local setup](#test-fineos-server-from-local-setup)
  - [1. Set up env values](#1-set-up-env-values)
  - [2. Local authentication](#2-local-authentication)
    - [2.1 If you are using Local API only (use Swagger UI)](#21-if-you-are-using-local-api-only-use-swagger-ui)
    - [2.2 If you are using Local Portal to Local API](#22-if-you-are-using-local-portal-to-local-api)
      - [Link Local Portal to Local API environment](#link-local-portal-to-local-api-environment)
      - [Login through a user account](#login-through-a-user-account)
  - [3. Data restrictions when interacting with Fineos](#3-data-restrictions-when-interacting-with-fineos)
    - [3.1 If you are testing as a Claimant](#31-if-you-are-testing-as-a-claimant)
    - [3.2 If you are testing as a Leave Admin](#32-if-you-are-testing-as-a-leave-admin)
      - [3.2.1: Change current user account to a leave admin account](#321-change-current-user-account-to-a-leave-admin-account)
      - [3.2.2: Verify current user as a leave admin for the claim's employer](#322-verify-current-user-as-a-leave-admin-for-the-claims-employer)
## 1. Set up env values

**Decide which FINEOS environment you wish to use. Paste and replace the following values in your `docker-compose.yml`**

<details>
  <summary>test - DT2</summary>

```
  - FINEOS_CLIENT_CUSTOMER_API_URL=https://dt2-api.masspfml.fineos.com/customerapi/
  - FINEOS_CLIENT_WSCOMPOSER_API_URL=https://dt2-api.masspfml.fineos.com/integration-services/wscomposer/
  - FINEOS_CLIENT_GROUP_CLIENT_API_URL=https://dt2-api.masspfml.fineos.com/groupclientapi/
  - FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL=https://dt2-api.masspfml.fineos.com/integration-services/
  - FINEOS_CLIENT_OAUTH2_URL=https://dt2-api.masspfml.fineos.com/oauth2/token
  - FINEOS_CLIENT_OAUTH2_CLIENT_ID=1ral5e957i0l9shul52bhk0037
  // no need to replace the following if you are using Swagger UI
  - COGNITO_USER_POOL_ID=us-east-1_HhQSLYSIe
  - COGNITO_USER_POOL_CLIENT_ID=7sjb96tvg8251lrq5vdk7de9
  - COGNITO_USER_POOL_KEYS_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_HhQSLYSIe/.well-known/jwks.json
```
</details>
<details>
  <summary>cps-preview - DT3</summary>

  ```
  - FINEOS_CLIENT_CUSTOMER_API_URL=https://dt3-api.masspfml.fineos.com/customerapi/
  - FINEOS_CLIENT_WSCOMPOSER_API_URL=https://dt3-api.masspfml.fineos.com/integration-services/wscomposer/
  - FINEOS_CLIENT_GROUP_CLIENT_API_URL=https://dt3-api.masspfml.fineos.com/groupclientapi/
  - FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL=https://dt3-api.masspfml.fineos.com/integration-services/
  - FINEOS_CLIENT_OAUTH2_URL=https://dt3-api.masspfml.fineos.com/oauth2/token
  - FINEOS_CLIENT_OAUTH2_CLIENT_ID=2gptm2870hlo9ouq70poib8d5g
  // no need to replace the following if you are using Swagger UI
  - COGNITO_USER_POOL_ID=us-east-1_1OVYp4aZo
  - COGNITO_USER_POOL_CLIENT_ID=59oeobfn0759c8166pjh381joc
  - COGNITO_USER_POOL_KEYS_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_1OVYp4aZo/.well-known/jwks.json
  ```
</details>
<details>
  <summary>stage - IDT</summary>

  ```
  - FINEOS_CLIENT_CUSTOMER_API_URL=https://idt-api.masspfml.fineos.com/customerapi/
  - FINEOS_CLIENT_WSCOMPOSER_API_URL=https://idt-api.masspfml.fineos.com/integration-services/wscomposer/
  - FINEOS_CLIENT_GROUP_CLIENT_API_URL=https://idt-api.masspfml.fineos.com/groupclientapi/
  - FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL=https://idt-api.masspfml.fineos.com/integration-services/
  - FINEOS_CLIENT_OAUTH2_URL=https://idt-api.masspfml.fineos.com/oauth2/token
  - FINEOS_CLIENT_OAUTH2_CLIENT_ID=1fa281uto9tjuqtm21jle7loam
  // no need to replace the following if you are using Swagger UI
  - COGNITO_USER_POOL_ID=us-east-1_HpL4XslLg
  - COGNITO_USER_POOL_CLIENT_ID=10rjcp71r8bnk4459c67bn18t8
  - COGNITO_USER_POOL_KEYS_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_HpL4XslLg/.well-known/jwks.json
  ```
</details>
<br/>

**Paste `FINEOS_CLIENT_OAUTH2_CLIENT_SECRET` from 1password7: `Fineos Client ID and Secrets`**

These are also available in [AWS SSM Parameter Store](https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table
) under `/service/pfml-api/${env}/fineos_oauth2_client_secret`
```
- FINEOS_CLIENT_OAUTH2_CLIENT_SECRET=...
```
<br/>

## 2. Local authentication

### 2.1 If you are using Local API only (use Swagger UI)

Follow [the instructions](/api#setting-up-local-authentication-credentials) in /api/README.md
<br/>

### 2.2 If you are using Local Portal to Local API 

#### Link Local Portal to Local API environment

in `portal/config` use the same Cognito ID information you used in `api/docker-compose.yml`

```
// development.js
apiUrl: "<http://localhost:1550/v1">

// default.js
cognitoUserPoolId: "{COGNITO_USER_POOL_ID}",
cognitoUserPoolWebClientId: "{COGNITO_USER_POOL_CLIENT_ID}",
```

#### Login through a user account

Option 1: Create a new account through the local portal directly

<details>
<summary> Option 2: Use an existing account from a deployed environment</summary>
If there is a Portal account you'd like to use which has existing information in the deployed FINEOS environment, we'll need to replicate the account in our local database using the email address and Cognito sub_id.

1. Log into the deployed Portal website; e.g. if you are targeting Fineos DT3, then use https://paidleave-cps-preview.eol.mass.gov/. For other environments, see [Environment URLs](https://lwd.atlassian.net/wiki/x/2oBEF).
2. Open console and run following command to get `sub_id`

```js
userDataCookie = document.cookie.split('; ')
  .find(cookie => cookie.match(/^CognitoIdentityServiceProvider.*userData=/))
  .split("=")[1];
JSON.parse(decodeURIComponent(userDataCookie))["UserAttributes"][0]["Value"]
```
3. Update user in local API DB
  - run `make create-user` if no user in your database
  - Use a SQL client or database shell(`make login-db`) to update the user row with email address you use in step 1 and sub_id from step 2
```sql
$ UPDATE user SET email_address="<EMAIL_YOU_USE_IN_STEP_1>", sub_id="<SUB_ID_FROM_STEP_2>" WHERE user_id="<CURRENT_USER_ID>";
```

1. Go to localhost:3000 and login with the same email and password
</details>

<br/>

 ## 3. Data restrictions when interacting with Fineos

At this point, we are ready to interact with Fineos from our local setup. Since Fineos is quite strict on the data they intake, we need to do a mark up of the data we use.

### 3.1 If you are testing as a Claimant

- Find a name, SSN & FEIN employee-employer combo to use from the [spreadsheet](https://docs.google.com/spreadsheets/d/1-t2CKi7X3FdZnatwuGVoYnKW6WQKjKCDAE7Jh4qaMhA/edit#gid=1920693753)

- Run `make generate-wagesandcontributions employer_fein=<employer_fein> employee_ssn=<employee_ssn>`

  - **IMPORTANT:**FEIN and SSN don’t require dashes and quotation marks, just numbers;
  - This command will create/update the employer record with fineos_employer_id: 1, so if you want to try a new combo, change the existing fineos_employer_id to other number. Otherwise you will get error like `(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "ix_employer_fineos_employer_id".` TODO (EMPLOYER-1677): https://lwd.atlassian.net/browse/EMPLOYER-1677

Now you can create an application with this name, SSN and FEIN, and test the flow through local portal or swagger UI. 
After submitting part 1, you can find the absence case in the Fineos Dashboard.

### 3.2 If you are testing as a Leave Admin

We don't have a script for this part, so please go to your database shell(`make login-db`) or use any PostgreSQL clients to modify the data.

#### 3.2.1: Change current user account to a leave admin account

Create a record in `link_user_role` table: 
```sql
INSERT INTO link_user_role (user_id, role_id) VALUES (<current_user_id>, 3);
```
<br />

#### 3.2.2: Verify current user as a leave admin for the claim's employer

When Leave admin reviews a claim, the claim data is from Fineos database and only accessible to a linked and verified employer account. So first, we need to link our current leave admin account to the employer/organization of the claim. 

1. Find an absence case from Fineos dashboard and go to the related employer page
   - If you are using a leave admin account linked to the employer of the claim, you could skip the following steps and retrieve the claim directly.
   - find the Identification Number, which is `employer_fein`
   - find a `Portal User ID` from the `points of contact` table
     - choose a row and click edit, and then copy `Portal User ID` from the edit page

2. Create/update an employer record 

```sql
INSERT INTO employer (employer_id, employer_dba, employer_fein) VALUES ( <random uuid>, "Fake name", <FEIN from step 1>);
```

3. Create a record in verification table: 

```sql
INSERT INTO verification (verification_id, verification_type_id) VALUES ( <random uuid>, 2);
```

4. Create a record in link_user_leave_administrator table:

```sql
INSERT INTO link_user_leave_administrator (user_id, employer_id, fineos_web_id, user_leave_administrator_id, verification_id) 
VALUES (<current_user_id>, <employer_id from step 2>, <Portal User ID from step 1>, <random uuid> , <verification_id from step 3>);
```
  This block can be tweaked based on the data model diagram below to address various test cases. Examples:
- Multiple records can be created to connect your leave admin user to multiple employers.
- The `fineos_web_id` can be left NULL to indicate a leave admin not yet registered in FINEOS.
- The `verification_id` can be left NULL to indicate an unverified leave admin.
Note in the last case that the leave admin will be unverifiable if there are no employer quarterly contributions for the employer in the DB, AKA taxes have not been paid yet or have not been filed and reported.

5. Create a record in claim table:

```sql
INSERT INTO claim (claim_id, employer_id, fineos_absence_id) VALUES ( <random uuid>, <employer_id from step 2>, <absence case id from step 1>);
```

At this point, you can get this claim from swagger UI or local portal. 

More information about how the Leave Admin data model tracks FINEOS registration and verification is below:

[Leave Administrator User States](https://lwd.atlassian.net/wiki/spaces/EMPLOYER/pages/1669300536/Leave+Administrator+User+States)

<img width="756" alt="Screen Shot 2021-07-19 at 10 38 13 AM" src="https://lucid.app/publicSegments/view/5d463dee-5466-43dc-8d60-5485d5d39ec6/image.jpeg">


