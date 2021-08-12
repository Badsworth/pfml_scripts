# Maintenance pages

The Portal includes the ability to have maintenance pages that we can turn on in case we need to shut down all or part of the website.

Maintenance pages are controlled through the `maintenance` entry in the [S3 feature-gate file](../../feature_flags/) corresponding to the environment.

To update the maintenance status, you should update the appropriate file (`feature_flags/test.yaml` to update the test environment) in a new branch. Once that branch is merged into the main branch, it will update the maintenance status on that environment due to the [Github workflow](../../.github/workflows/feature-flags-sync.yml) that will sync the yaml files in that directory to s3.

The data is retrieved from the file via API request in the portal and then set in `appLogic.featureFlags.flags`. The API request is cached for five minutes and only executed once for every full page request (not on react render/re-render).

It may take up to 20 minutes for the portal to read the updated maintenance status due to s3 file caching in the API and the browser caching the API response.


All available options for maintenance are:

```yaml
maintenance:
  start: <ISO 8601 timestamp>
  end: <ISO 8601 timestamp>
  enabled: 0
  options:
    page_routes:
      - /*
```

Add the `options:page_routes` key to the environment you want to target. It accepts an array of routes (without trailing slashes) that should render a maintenance page. The maintenance page will render on all routes by default if `page_routes` is omitted.

## Enable site wide

Use `*` to match any string:

```yaml
enabled: 1
options:
  page_routes:
    - /*
```

## Enable on a group of pages

```yaml
enabled: 1
options:
  page_routes:
    - /applications/*
```

## Enable on specific pages

```yaml
enabled: 1
options:
  page_routes:
    - /create-account
```

## Enable scheduled maintenance page

If the maintenance page is being added because of scheduled down time, you can optionally schedule the beginning and end of this maintenance time by setting the `start` and/or `end` keys to an [ISO 8601](https://xkcd.com/1179/) datetime string.

- Daylight savings time needs taken into account! For Eastern Daylight Time (EDT), use `-04:00`, for Eastern Standard Time (EST), use `-05:00`.
- The start and end time are optional.
  - If start time is not set, the start time begins immediately.
  - If end time is not set, an engineer will need to manually turn off the maintenance page.
  - When end time is set, it will be displayed to the user using their timezone and localization preferences.

For example, to enable the maintenance page on all routes, starting at March 25 at 3:30am EDT and ending at March 26 at 8pm EDT.

```yaml
start: "2021-03-25T03:30:00-04:00"
end: "2021-03-26T20:00:00-04:00"
enabled: 1
options:
  page_routes:
    - /*
```

We're using Eastern time zone above since that's what Massachusetts is, but it could technically be whatever timezone.


## Disable site wide

Any time `enabled: 0` is set for maintenance, the maintenance status is disabled for the entire site. Disabling maintenance is very similar to enabling maintenance. Set `enabled: 0` in the relevant feature flag file for the environment in a new branch. Once the PR is merged into main, the maintenance status will be disabled on that environment within 20 minutes.

## Testing

If you are testing the configuration locally, just note that you need to restart the local development server in order for new environment variables to kick in.

## Bypassing maintenance pages

It can be helpful to bypass a maintenance page to test the page itself. To do so, you can enable the `noMaintenance` [feature flag](feature-flags.md) in the browser.

For example, to bypass the maintenance pages in the Test environment: `https://paidleave-test.mass.gov?_ff=noMaintenance:true`
