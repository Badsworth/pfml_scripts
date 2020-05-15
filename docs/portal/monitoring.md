# Monitoring

We use [New Relic Browser](https://newrelic.com/products/browser-monitoring) to monitor errors in our application. This works by including [a JS snippet](https://docs.newrelic.com/docs/browser/new-relic-browser/installation/install-new-relic-browser-agent#copy-paste-app) towards the top of our HTML. This snippet works out of the box by wrapping low-level browser APIs, and globally exposes [an API (`newrelic`) for explicitly tracking](https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api) interactions and errors that the app catches itself.

## Environments

Each environment requires its own New Relic Browser "app" in order for us to differentiate between data coming in from the different environments. Create these through the New Relic site. Each New Relic app has its own `applicationId`, which will need set as part of the JS snippet included in our HTML.

[CP-417](https://lwd.atlassian.net/browse/cp-417) is tracking the work to create New Relic apps for each environment.

## Enabling New Relic Browser

If you have a browser extension installed to block trackers, you may need to safelist the New Relic snippet to allow it to make requests. If it's not being blocked, then it should Just Work. You can verify this by viewing the Network tab in DevTools, and observe payloads occasionally being sent to `bam.nr-data.net`

## Related

- [Error monitoring research](https://lwd.atlassian.net/wiki/spaces/DD/pages/229835319/Error+Monitoring+Research)
