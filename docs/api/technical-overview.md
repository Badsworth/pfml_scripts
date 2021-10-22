# Technical Overview

- [Key Technologies](#key-technologies)
- [Request operations](#request-operations)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Running In Hosted Environments](#running-in-hosted-environments)
  - [ECS](#ecs)

## Key Technologies

The API is written in Python, utilizing Connexion as the web application
framework (with Flask serving as the backend for Connexion). The API is
described in the OpenAPI Specification format in the file
[openapi.yaml](/api/openapi.yaml).

SQLAlchemy is the ORM, with migrations driven by Alembic. pydantic is used in
many spots for parsing data (and often serializing it to json or plain
dictionaries). Where pydantic is not used, plain Python dataclasses are
generally preferred.

- [OpenAPI Specification][oas-docs]
- [Connexion][connexion-home] ([source code][connexion-src])
- [SQLAlchemy][sqlalchemy-home] ([source code][sqlalchemy-src])
- [Alembic][alembic-home] ([source code](alembic-src))
- [pydantic][pydantic-home] ([source code][pydantic-src])
- [poetry](https://python-poetry.org/docs/) - Python dependency management

[oas-docs]: http://spec.openapis.org/oas/v3.0.3
[oas-swagger-docs]: https://swagger.io/docs/specification/about/

[connexion-home]: https://connexion.readthedocs.io/en/latest/
[connexion-src]: https://github.com/zalando/connexion

[pydantic-home]:https://pydantic-docs.helpmanual.io/
[pydantic-src]: https://github.com/samuelcolvin/pydantic/

[sqlalchemy-home]: https://www.sqlalchemy.org/
[sqlalchemy-src]: https://github.com/sqlalchemy/sqlalchemy

[alembic-home]: https://alembic.sqlalchemy.org/en/latest/
[alembic-src]: https://github.com/sqlalchemy/alembic


## Request operations

- OpenAPI spec (`openapi.yaml`) defines API interface: routes, requests, responses, etc.
- Connexion connects routes to handlers via `operationId` property on a route
    - Connexion will run OAS validations before reaching handler
    - Connexion will run authentication code and set user in the request context
    - The handlers generally live in the top level files at
      [massgov/pfml/api](/api/massgov/pfml/api/), with the `operationId` pointing
      to the specific module and function
- Handlers check if user in request context is authorized to perform the action
  the request represents
- Handlers use pydantic models to parse request bodies and construct response data
- Connexion will run OAS validations on response format from handler

## Authentication

Authentication methods are defined in the `securitySchemes` block in
`openapi.yaml`. A particular security scheme is enabled for a route via a
`security` block on that route. Note the `jwt` scheme is enabled by default for
every route via the global `security` block at the top of `openapi.yaml`.

Connexion runs the authentication before passing the request to the route
handler. In the `jwt` security scheme, the `x-bearerInfoFunc` points to the
function that is run to do the authentication.

## Authorization

Authorization is handled via the
[bouncer](https://github.com/bouncer-app/bouncer) and
[flask-bouncer](https://github.com/bouncer-app/flask-bouncer) libraries.

The rules are defined in
[massgov/pfml/api/authorization/rules.py](/api/massgov/pfml/api/authorization/rules.py),
and request handlers use the `ensure` and `can` functions provided by
flask-bouncer (re-exported in
[massgov/pfml/api/authorization/flask.py](/api/massgov/pfml/api/authorization/flask.py)
for use in the application, as we may eventually want to provide slightly
modified versions of the functions provided by flask-bouncer directly) to check
if the user in the current request context is authorized to perform the given
action on the given subject.


## Running In Hosted Environments

Application code gets run as tasks on [AWS Elastic Container Service (ECS)
clusters][ecs-docs], backed by [AWS Fargate][fargate-docs]

[ecs-docs]: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html
[fargate-docs]: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html

For actually performing deploys, see [/docs/deployment.md](/docs/deployment.md).

### ECS

ECS tasks all share the same container as built by the `app` stage of the
`Dockerfile`. This stage builds the project Python package (basically zip up
[massgov/](/api/massgov)) and installs it into the container environment.

This also has the effect of making the package entrypoints as listed in the
`[tool.poetry.scripts]` section of [pyproject.toml](/api/pyproject.toml)
available on `PATH`, so ECS tasks besides the Paid Leave API server tend to set
one of these as their Docker command.

The Paid Leave API server ECS task is declared in
[/infra/api/template/service.tf](/infra/api/template/service.tf) as well as its
ECS service, which is a wrapper for ECS tasks to ensure a specified number of
the tasks are running, provides mechanisms for autoscaling, and various other
"service" features.

Other ECS tasks are in
[/infra/ecs-tasks/template/tasks.tf](/infra/ecs-tasks/template/tasks.tf). These
are not a part of an ECS service, the tasks are launched/started on demand
(either by an automated process like a scheduled AWS EventBridge event, Step
Function, or manually through the [/bin/run-ecs-task](/bin/run-ecs-task/) tool).
