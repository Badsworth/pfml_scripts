# Maintenance pages

The Portal includes the ability to have maintenance pages that we can turn on in case we need to shut down all or part of the website.

Maintenance pages are controlled through the `maintenancePageRoutes` [environment variable](environment-variables.md).

Add the `maintenancePageRoutes` variable to the environment you want to target. It accepts an array of routes (without trailing slashes) that should render a maintenance page.

## Enable site wide

Use `*` to match any string:

```json
"maintenancePageRoutes": ["/*"]
```

## Enable on a group of pages

```json
"maintenancePageRoutes": ["/applications/*"]
```

## Enable on specific pages

```json
"maintenancePageRoutes": [
  "/create-account",
  "/employers/create-account"
]
```

## Testing

If you are testing the configuration locally, just note that you need to restart the local development server in order for new environment variables to kick in.

## Bypassing maintenance pages

It can be helpful to bypass a maintenance page to test the page itself. To do so, you can enable the `noMaintenance` [feature flag](feature-flags.md) in the browser.

For example, to bypass the maintenance pages in the Test environment: `https://paidleave-test.mass.gov?_ff=noMaintenance:true`
