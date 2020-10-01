During development of the Portal, there are common tasks an API or Portal engineer may need to perform within the API codebase.

## Adding fields

1. Add the field to the DB model: `db/models/applications.py`
1. [Generate a new migration file](../../api/README.md#creating-new-migrations)

See below for how to allow this field in API requests and responses.

## Accept fields in requests

> Application fields should be `nullable` / `Optional` to support the Portal sending partial request bodies in its multi-page flows.

1. Add the field to the `openapi.yaml` spec.
1. Add the field to the [`requests.py`](../../api/massgov/pfml/api/models/applications/requests.py) API Application model
1. Add test coverage to assert the new field is persisted in the DB.

## Include fields in responses

1. Add the field to the `openapi.yaml` spec
1. Add the field to the [`responses.py`](../../api/massgov/pfml/api/models/applications/responses.py) API Application model
1. Add test coverage to assert the new field is included in responses.

## Adding validations

Basic validation is achieved using the Open API spec, using keywords such as:

- [`type`](https://swagger.io/docs/specification/data-models/data-types/)
- [`format`](https://swagger.io/docs/specification/data-models/data-types/#string)
- [`pattern`](https://swagger.io/docs/specification/data-models/data-types/#pattern)
- [`enum`](https://swagger.io/docs/specification/data-models/enums/)

### "Required" fields

TODO: Document how validations are added for required or conditionally required fields: https://github.com/EOLWD/pfml/pull/1130
