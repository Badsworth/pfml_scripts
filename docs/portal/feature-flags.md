# Feature flags

[Original tech spec for feature flags is available on Confluence](https://lwd.atlassian.net/wiki/x/4oAPD)

## Defining feature flags

Feature flags are defined in `portal/config/featureFlags.js`. These flags are then set as environment variables in `portal/next.config.js` at initial build time (so they don't live reload when running locally). **If you define a new feature flag during local development, you will need to restart the dev server in order for the flag to become available**.

Feature flags should be named so that the absence of a default value is interpreted as `false` – this way if someone forgets to define a feature flag, it doesn’t unintentionally enable the feature for everyone.

## Checking a feature flag

The `src/utils/isFeatureEnabled.js` function can be used to check if a feature flag is enabled:

```js
if (isFeatureEnabled("showExample")) {
  return "This is an example";
}
```
