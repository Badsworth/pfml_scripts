# Massachusetts PFML API Layer

- [Introduction](#introduction)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Setting up local authentication credentials](#setting-up-local-authentication-credentials)
  - [User authentication](#user-authentication)
  - [Machine-to-machine authentication via Swagger UI](#machine-to-machine-authentication-via-swagger-ui)
- [Seed your database](#seed-your-database)

**More detailed information:**

- [API Technical Overview](../docs/api/technical-overview.md)
- [Development Environment Setup](../docs/api/development-environment-setup.md)
- [Database Migrations](../docs/api/database-migrations.md)
- [Running the Application (Docker)](../docs/api/running-the-application-docker.md)
- [Automated Tests](../docs/api/automated-tests.md)
- [Working With Releases](../docs/api/working-with-releases.md)
- [API Monitoring](../docs/api/monitoring.md)

**You may also be interested in:**

- [Setting up project tooling](../README.md)
- [Development practices](../docs/contributing.md)
- [Adding fields and validations](../docs/api/fields-and-validations.md)
- [Additional API-specific documentation](../docs/api/)

## Introduction

This is the API layer for the Massachusetts Paid Family and Medical Leave program. It includes a few separate system components:

- The Paid Leave REST API
- A series of background data pipelines that can be scheduled or manually triggered
- Some manually-executed utility scripts

The API Layer is used by two front-end web applications.

- Claimant Portal
- Leave Admin

Additional information about [PFML system components](https://lwd.atlassian.net/wiki/spaces/API/pages/438240043/Components) can be found in confluence.


## Directory Structure

```
.
├── massgov                     Python package directory
│   └── pfml
│       └── api                 Application code
│       └── db
│           └── migrations      Migrations config
│               └── versions    Migrations themselves
├── tests
│   └── api             Application tests
├── Dockerfile          Multi-stage Docker build file for project
├── docker-compose.yml  Config file for docker-compose tool, used for local development
├── openapi.yaml        API specification
├── pyproject.toml      Python project configuration file
├── newrelic.ini        New Relic configuration file
└── setup.cfg           Python config for tools that don't support pyproject.toml yet
```


## Getting Started

0. Install [Docker](https://docs.docker.com/get-docker)
1. `cd pfml/api` (or otherwise move to this directory)
2. `make init`
3. `make start`

Your application should be running now.  Try it out!  A UI is available at [http://localhost:1550/v1/docs/](http://localhost:1550/v1/docs/)

The OpenAPI spec is available at:

- [http://localhost:1550/v1/openapi.json](http://localhost:1550/v1/openapi.json) (JSON) or
- [http://localhost:1550/v1/openapi.yaml](http://localhost:1550/v1/openapi.yaml) (YAML)
 

**Next steps:**

- [Set up local authentication credentials](#setting-up-local-authentication-credentials)
- [Seed your database](#seed-your-database)
- Review documentation in `/docs`, especially [contributing.md](../docs/contributing.md) for guidelines on how to contribute code
- Read the [technical overview](../docs/api/technical-overview.md) to understand how API components work.


## Setting up local authentication credentials

### User authentication

In order to make requests to the API, an authentication token must be included.
Currently this is a JWT set in the `Authorization` HTTP header. A JWT signed by
a locally generated JWK can be created for a user via:

```sh
make jwt auth_id=<sub_id of a user record>
```

Currently the JWT expires after a day, but we may tweak the lifetime for
convenience at some point.

If a user doesn't already exist, can create a random user in the database with:

```sh
make create-user
```

Which will print something like:

```
{'user_id': '548c9e28-3d72-4c5c-96e7-4a77f3c37041',
 'sub_id': '33f965ad-0150-4c5b-a3a6-86bbd5df1a26',
 'email_address': 'gfarmer@lewis.com',
 'consented_to_data_sharing': False}
```

The `sub_id` field is what is needed to generate a JWT. For the
example above, it would be:

```sh
make jwt auth_id=33f965ad-0150-4c5b-a3a6-86bbd5df1a26
```

Which will print something like:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1OTI0OTQxOTIsInN1YiI6IjMzZjk2NWFkLTAxNTAtNGM1Yi1hM2E2LTg2YmJkNWRmMWEyNiJ9.KMze0GfJ9cQ10e9G27vcOgn3nBiqhXxxtCBZYIgScFo
```

That value should be included as a bearer token in the `Authorization` header of
requests.

On the documentation pages mentioned in the section above, click the "Authorize"
button and paste the above value. After that every request sent from the docs
page will be authenticated with that token.

For individual requests via `curl` or similar:

```sh
curl -v --header "Authorization: Bearer <big jwt string above>" http://localhost:1550/v1/users/current
```

### Machine-to-machine authentication via Swagger UI

When testing with the Swagger UI, some endpoints require a `client_id` and `client_secret`. This is not necessary when making requests directly via `curl` or other tools, where the `Authorization` header is the only prerequesite.  For these, you will need to configure your environment to point to a real Cognito resource:

1. Copy credentials in the ["Testing" section of this Confluence page](https://lwd.atlassian.net/l/c/CRjiWu8L), you'll need these for later steps.
1. Update the `COGNITO_USER_POOL_KEYS_URL` setting in `docker-compose.yml` to point to one of our environments. There should be one already in the file that you can uncomment.
1. Update `tokenUrl` in the `openapi.yaml` to the Cognito address (for stage: `https://massgov-pfml-stage.auth.us-east-1.amazoncognito.com/oauth2/token`)
1. Create a user: `make create-user args=fineos` 
1. In a tool like Postico, edit the DB record for the user, and change its `sub_id` to the `client_id`
1. Re-build and restart the Docker container


## Seed your database

Some interactions require valid data and associations to exist within the database, such as a valid `Employer` and `Employee`. 

To create a leave admin user account with claims, run:

```
make create-leave-admin-and-claims
```

The script above will output information you can use to then generate the JWT, which you can use in Swagger to perform API requests as the generated leave admin.

Another way to seed your database is to run a mock DOR import:

Generate a fake DOR file:

```
make dor-generate
```

Run the DOR import locally:

```
make dor-import
```

After the scripts above have ran, you can grab values from your database tables using a tool like [Postico](https://eggerapps.at/postico/).
