During development of the Portal, there are common tasks an API or Portal engineer may need to perform within the API codebase.

## Adding fields

1. Add the field to the DB model: `db/models/applications.py`
1. [Generate a new migration file](../../api/README.md#creating-new-migrations)

See below for how to allow this field in API requests and responses.

### Accept fields in requests

> Application fields should be `nullable` / `Optional` to support the Portal sending partial request bodies in its multi-page flows.

1. Add the field to the `openapi.yaml` spec.
1. Add the field to the [`requests.py`](../../api/massgov/pfml/api/models/applications/requests.py) API Application model
1. Add test coverage to assert the new field is persisted in the DB.

### Include fields in responses

1. Add the field to the `openapi.yaml` spec
1. Add the field to the [`responses.py`](../../api/massgov/pfml/api/models/applications/responses.py) API Application model
1. Add test coverage to assert the new field is included in responses.

## Validation rules

### Validation Rules vs. Eligibility Rules

We should distinguish validation rules from eligibility rules. It’s one thing to automatically deny someone eligibility based on some eligibility criteria (like child birth date being within 12 months) and then allowing that person to appeal (if they have some valid extenuating circumstances), and it’s an entirely different thing to prevent them from applying altogether claiming that the application isn’t even a valid application.

**Validation should only serve to help prevent incorrect data (typos, etc) not prevent ineligible applications**. We should be careful not to accidentally deny a claimant’s right to an appeal or otherwise make the system less flexible than it needs to be as is so often the case with government systems.

### Adding validation rules

#### OpenAPI

OpenAPI includes keywords that help enforce a subset of validation rules, primarily:

- [`type`](https://swagger.io/docs/specification/data-models/data-types/)
- [`format`](https://swagger.io/docs/specification/data-models/data-types/#string)
- [`pattern`](https://swagger.io/docs/specification/data-models/data-types/#pattern)
- [`enum`](https://swagger.io/docs/specification/data-models/enums/)

For all endpoints, these validations always result in a 400 status code with `errors` when a rule is not fulfilled.

These validations are located in the `openapi.yml` spec file.

#### Pydantic custom validators

[Pydantic custom validators](https://pydantic-docs.helpmanual.io/usage/validators/) are used for enforcing more complex validation logic, such as business rules or reality checks on a single field(e.g a birthdate must be in the past).

For all endpoints, these validations always result in a 400 status code with `errors` when a rule is not fulfilled.

These validations are located in `requests.py`.

#### Required and cross-field validations

A `get_application_issues` function also exists for reporting potential "warnings" on an application. These are primarily rules related to required or conditionally required fields, but may also relate to rules that span multiple fields.

For `GET` and `PATCH` requests to the `/applications/:application_id` endpoint, these validations result in data still saving to our database and a 200 status code with `warnings` rather than `errors`, since we expect requests to not always have a complete application, since a user will be filling out the application through a multi-page experience.

For `POST` requests to /applications/:application_id/complete_application and /applications/:application_id/submit_application, these validations result in a 400 status code with `errors` when a rule is not fulfilled.

These validations are located in `application_rules.py`.
