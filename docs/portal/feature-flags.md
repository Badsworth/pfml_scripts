# Feature flags

[Original tech spec for feature flags is available on Confluence](https://lwd.atlassian.net/wiki/x/4oAPD). 

Note that a seperate system is currently maintained for maintenance pages; see [Maintenance Pages](./maintenance-pages.md) and [Feature Gate Flags](../../feature_flags/).

## Defining feature flags

Feature flags are defined in [`portal/config/featureFlags.js`](../../portal/config/featureFlags.js). These flags are then set as environment variables in `portal/next.config.js` at initial build time (so they don't live reload when running locally). **If you define a new feature flag during local development, you will need to restart the dev server in order for the flag to become available**.

Feature flags should be named so that the absence of a default value is interpreted as `false` – this way if someone forgets to define a feature flag, it doesn’t unintentionally enable the feature for everyone.

## Checking feature flags in the code

The `services/featureFlags.js` file includes methods for checking the value of a feature flag, as well as a method for overriding environment-level feature flags through the URL's query string.

The `isFeatureEnabled` method can be used to check if a feature flag is enabled:

```js
if (isFeatureEnabled("showExample")) {
  return "This is an example";
}
```

## Overriding a feature flag in the browser

Cookies are used for overriding an environment's default feature flag.

To do so, add a query param of `_ff` to the site's URL and use JSON notation for its value. A feature flag's value can be `true`, `false`, or `reset`. Setting a flag to reset will restore it to the environment's default.

For example:

- To **enable** a feature flag called `unrestrictedClaimFlow`, you would visit:
  `{Site URL}?_ff=unrestrictedClaimFlow:true`
- To **disable** a feature flag called `unrestrictedClaimFlow`, you would visit:
  `{Site URL}?_ff=unrestrictedClaimFlow:false`
- To **reset** a feature flag called `unrestrictedClaimFlow`, you would visit:
  `{Site URL}?_ff=unrestrictedClaimFlow:reset`

You can also manage multiple flags by separating their key/value pairs with a `;`. For example:
`{Site URL}?_ff=unrestrictedClaimFlow:true;anotherFlag:true`

### Preventing / Allowing the site to be rendered

While the site is under development, [we don't want it to be visible to the press or the public](https://lwd.atlassian.net/browse/CP-459). As a low-tech solution, we use a feature flag prefixed with `pfml` to determine whether the site should be rendered.

**To render the site, enable the `pfmlTerriyay` flag** by visiting: `{Site URL}?_ff=pfmlTerriyay:true`

⚠️ The exact flag name may change if we need to force the site to be hidden for people who previously enabled the flag through through browser. If the above flag doesn't work, you should check [`config/featureFlags.js`](../../portal/config/featureFlags.js) to verify whether it's still the correct flag name we're using.
