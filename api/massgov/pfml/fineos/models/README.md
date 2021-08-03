# Generating models from FINEOS OpenAPI Spec

We use OpenAPI JSON specs from FINEOS to generate Pydantic models for use in PFML.  The automated script generates some base models, which we then extend further with our custom changes.  See instructions below for making updates.

## General steps

1. Manually retrieve spec files from [FINEOS documentation - credentials required](https://documentation.fineos.com/support/documentation/).  **Note:** These used to be `.yaml` files but now are avaiable as JSON.

    - FINEOS Customer API
    - FINEOS Group Client API

1. Optionally preprocess them to standardize some values.  The JSON will have some values like `"format": "date-time"` which is invalid.  The preprocessor will convert this to `"format": "date"`, as well as some other values.

    ```
    make customer_api/spec.cleaned.json
    make group_client_api/spec.cleaned.json
    # Looks for <customer_api|group_client_api>/spec.json to produce <customer_api|group_client_api>/spec.cleaned.json
    ```

   If you unexpectedly get a message like the following, delete the generated `*.cleaned.json` and run the `make` command again.
   
      ```
      make: `customer_api/spec.cleaned.json' is up to date.
      ```

1. Generate python base classes using the cleaned JSON spec

    ```
    make customer_api/spec.py
    make group_client_api/spec.py
   # Looks for <customer_api|group_client_api>/spec.cleaned.json to produce <customer_api|group_client_api>/spec.pt
    ```
   
    **Note:** Pydantic will try to handle data formats it doesn't understand by defaulting to `string`.  The preprocessor in the previous step attempts to mitigate some of this.
   
## Updating

When updating from new versions of FINEOS specs, retrieve the new spec JSON from the documentation site and run `make models`.

- You may need to manually update the corresponding `__init__.py` if there are new classes to expose in our API.
