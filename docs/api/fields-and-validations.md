During development of the Portal, there are common tasks an API or Portal engineer may need to perform within the API codebase.

## Adding fields

1. Add the field to the DB model: `db/models/applications.py`
1. [Generate a new migration file](../../api/README.md#creating-new-migrations)

See below for how to allow this field in API requests and responses.

### Accept fields in requests

> Application fields should be `nullable` / `Optional` to support the Portal sending partial request bodies in its multi-page flows.

1. Add the field to the `openapi.yaml` spec.
1. Add the field to the [`requests.py`](../../api/massgov/pfml/api/models/applications/requests.py) Pydantic model
1. Add test coverage to assert the new field is persisted in the DB.

### Include fields in responses

1. Add the field to the `openapi.yaml` spec
1. Add the field to the [`responses.py`](../../api/massgov/pfml/api/models/applications/responses.py) Pydantic model
1. Add test coverage to assert the new field is included in responses.

## Validation rules

### Validation Rules vs. Eligibility Rules

We should distinguish validation rules from eligibility rules. It’s one thing to automatically deny someone eligibility based on some eligibility criteria (like child birth date being within 12 months) and then allowing that person to appeal (if they have some valid extenuating circumstances), and it’s an entirely different thing to prevent them from applying altogether claiming that the application isn’t even a valid application.

**Validation should only serve to help prevent incorrect data (typos, etc) not prevent ineligible applications**. We should be careful not to accidentally deny a claimant’s right to an appeal or otherwise make the system less flexible than it needs to be as is so often the case with government systems.

### Adding validation rules

Validation rules currently are enforced at three different layers:

1. OpenAPI generally enforces a subset of rules on individual fields
1. Pydantic models enforce some business rules on individual fields
1. Custom code enforces presence of required fields or rules requiring context of multiple fields

#### OpenAPI

OpenAPI is the first layer a request flows through, and enforces a subset of validation rules:

- [`type`](https://swagger.io/docs/specification/data-models/data-types/)
- [`format`](https://swagger.io/docs/specification/data-models/data-types/#string)
- [`pattern`](https://swagger.io/docs/specification/data-models/data-types/#pattern)
- [`enum`](https://swagger.io/docs/specification/data-models/enums/)

For all endpoints, these validations always result in a 400 status code with `errors` when a rule is not fulfilled.

These validations are located in the `openapi.yml` spec file.

**Why we avoid [OpenAPI's `required` property](https://swagger.io/docs/specification/data-models/data-types/#required)**

To display a user friendly internationalized error message to Portal users, the error must include the `field` that is missing and a consistent `type`. For example:

```json
{
  "errors": [
    {
      "field": "password",
      "type": "required"
    }
  ]
}
```

OpenAPI pitfalls:

- The main deal breaker is when using the OpenAPI's `required` property, the error response [doesn't return the name of the specific field that is missing](https://github.com/Julian/jsonschema/issues/119). It just returns the full array of fields that are required. This prevents Portal from displaying a useful error message.
- Some endpoints are split across multiple pages in the Portal so it will be expected that not all required fields are present at once in a request.

#### Pydantic field validator

Individual fields on a Pydantic model can have [custom validation logic](https://pydantic-docs.helpmanual.io/usage/validators/) to enforce business rules or reality checks (e.g a birthdate must be in the past). These validators can raise a `ValidationException` to cause the API endpoint to respond with a 400 response with `errors`.

#### Required fields and cross-field validations

Our current approach is to use custom code is enforce the presence of fields, or more complex validation logic dependent on the values of multiple fields.

The current convention for this set of validations is to:

- Create a `*_rules.py` module (e.g `user_rules.py`) for the endpoints' validation logic
- Add `get_*_issues` method for validating an endpoint
- Call `get_*_issues` with the API request and check if there are any issues returned

---

### How Application validation works

A `get_application_submit_issues` function exists for reporting potential "warnings" on an application at the time part 1 is submitted. These are primarily rules related to required or conditionally required fields, but may also relate to rules that span multiple fields.

For `GET` and `PATCH` requests to the `/applications/:application_id` endpoint, these validations result in data still saving to our database and a 200 status code with `warnings` rather than `errors`, since we expect requests to not always have a complete application, since a user will be filling out the application through a multi-page experience.

For `POST` requests to `/applications/:application_id/*` endpoints, these validations result in a 400 status code with `errors` when a rule is not fulfilled.

These validations are located in `application_rules.py`.
