# Data Generation - Technical Documentation

All ad-hoc data generation tasks are done using a Typescript file stored in `src/scripts`. Each ticket we work on typically gets its own script, which we commit to the repository for historical reference. A single script might do any or all of the following:

- Generate Employer Data, stored in JSON files and optionally exported to DOR employer files.
- Generate Employee Data, stored in JSON files and optionally exported to DOR employee files.
- Generate Claim Data, stored in JSON files.
- Submit claims to the API, and optionally "post process" those claims by performing adjudication actions in Fineos.

### Concepts used in data generation scripts

- **Data Directory**: A data directory is a directory on the filesystem where we store generated data during generation and submission. It typically ends up with at least an `employees.json` and `employers.json` file in it, and often includes DOR files and `claims.json` as well.
- **Employee/Employer/Claim Pools**: A "pool" is a collection of generated data that can be loaded from and saved to the filesystem in the form of a JSON (or NDJSON, for claims) file.
- **Scenarios**: A scenario is a specification for how a claim will be generated and what kind of employee will be used. It can specify things like the claim's start and end date, type, leave reason, etc. During claim generation, claims from multiple scenarios can be combined into the final claim pool.

### Examples

All data generation scripts use APIs which are defined in `src/generation` and `src/submission`. The best way to explain those APIs is probably to point to examples of specific scripts we've used in the past:

- [E2E test Employer and Employee generation](../src/scripts/2021-04-08-e2e-employees.ts): This script generates 5 employers and 10,000 employees. All employees are assigned to 2 of the employers (the other 3 are just used for LA registration/verification testing). This script generates the JSON files, as well as DOR files, which we then loaded into every environment.
- [PUB payment testing generation & submission](../src/scripts/2021-04-02-payments.ts): This script generates claim data using complex scenarios that were defined for this task (employees/employers are generated externally). It also defines a claim submission routine, including post-submission adjudication action.

### Common commands

Note: Some of the dataset commands require AWS credentials. The easiest way to deal with these credentials is use AWS SSO:

1. Setup AWS SSO using the [instructions here](https://github.com/EOLWD/pfml/blob/main/docs/infra/1-first-time-setup.md#configuring-aws-sso). Tip: use a memorable `profile` name for the SSO profile, like `pfml`, so it's easy to type later on.
2. Run `aws sso login --profile pfml`, which will open your browser to perform the SSO login and grab a set of temporary credentials.
3. Run any of the commands below, adding `AWS_PROFILE=pfml` before them to trigger using the SSO profile and credentials.

#### Upload a new dataset, process it, register LAs, and employer addresses

```shell
npm run cli -- dataset deploy --directory ./data/the-dataset --environment test
```

#### DOR file upload/ETL

```bash
npm run cli -- dataset upload --directory ./data/the-dataset --environment test
```

#### Leave Admin Registration

```bash
npm run cli -- dataset register-las --directory ./data/the-dataset --environment test
```

#### Registering Employer Addresses

```bash
npm run cli dataset register-er-addresses --directory ./data/the-dataset --environment test
```

#### Claim Submission

Needs a folder with a `claims.ndjson` file

```bash
E2E_ENVIRONMENT=${env} npm run cli -- simulation submit data/${folder} --cc 3 --verbose=true
```

#### Running Generation Scripts

```bash
npx ts-node src/scripts/2021-04-08-e2e-employees.ts
```
