# Address validation

We use [Experian's REST API for address validation](https://docs.experianaperture.io/address-validation/experian-address-validation/). 

Address validation happens in 2 steps. 1 request that fetches a list of address suggestions based on an address search value (`/search` endpoint), and another that retrieves the address details of a given address. (`/format` endpoint)

The `/search` result returns a confidence level of `Verified match` , `Multiple matches`, `No matches`, or `Insufficient search terms`.

Experian has a self-service portal where DFML Solution Architects manage authentication tokens. We’ve created 2 tokens: 1 secret token for local testing, and 1 public token that restricts requests to paidleave-{env}.mass.gov URLs. 

## Testing

The secret token for local testing can not be shared or included in environment variables, but you can find it in [SSM](https://console.aws.amazon.com/systems-manager/parameters/service/pfml-api/experian-portal-auth-token/description?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:experian). Create a `portal/.env.local` file and add `NEXT_PUBLIC_experianApiKey=XXXXXXXXXX` as an environment variable ([see next docs](https://nextjs.org/docs/basic-features/environment-variables#exposing-environment-variables-to-the-browser)).

Address validation will be turned off in test and stage environments by default, but you can test it locally by enabling the `claimantValidateAddress` feature flag. 