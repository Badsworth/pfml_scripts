# Monitoring

We use [New Relic Browser](https://newrelic.com/products/browser-monitoring) to monitor errors in our application. This works by including [a JS snippet](https://docs.newrelic.com/docs/browser/new-relic-browser/installation/install-new-relic-browser-agent#copy-paste-app) towards the top of our HTML. This snippet, `new-relic.js`, works out of the box by wrapping low-level browser APIs, and globally exposes [an API (`newrelic`) for explicitly tracking](https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api) interactions and errors that the app catches itself.

## New Relic

### Configuration

The New Relic snippet requires each environment to include a `newRelicAppId` environment variable with the New Relic Browser Application ID.

We configure the New Relic snippet by setting the `window.NREUM` global variable, in `_document.js`, before loading the New Relic snippet.

🚨 If we ever update the New Relic snippet, we should ensure that the configuration portion at the bottom is removed, so that we're not overwriting `window.NREUM.loader_config` or `window.NREUM.info`.

### JS Errors

New Relic Browser is used for monitoring JS Errors. JS Errors are reported to New Relic in a variety of ways:

1. When we add a `try/catch` statement, we _should_ call the `newrelic` API's `noticeError` method. For example:
   ```js
   try {
     await doSomething();
   } catch (error) {
     tracker.noticeError(error);
   }
   ```
1. Our `ErrorBoundary` component catches any errors that bubble up from its descendant child components
1. The New Relic snippet should automatically catch errors that our React app doesn't catch

Errors caught by our `ErrorBoundary` component are reported to New Relic and also include a `componentStack` custom attribute, which provides additional information about which component threw the error.

New Relic Browser's UI only displays the error's stack trace, so if you want to view the `componentStack` value, you'll need to use [NRQL](https://docs.newrelic.com/docs/query-data/nrql-new-relic-query-language/getting-started/nrql-syntax-clauses-functions) to query the `JavaScriptError`:

```sql
SELECT timestamp, componentStack, stackTrace FROM JavaScriptError WHERE appName = 'PUT THE APP NAME HERE'
```

### Environments

Each environment requires its own New Relic Browser "app" in order for us to differentiate between data coming in from the different environments. Create these through the New Relic site. Each New Relic app has its own `applicationId`, which will need set as part of the JS snippet included in our HTML.

[CP-417](https://lwd.atlassian.net/browse/cp-417) is tracking the work to create New Relic apps for each environment.

### Enabling New Relic Browser

If you have a browser extension installed to block trackers, you may need to safelist the New Relic snippet to allow it to make requests. If it's not being blocked, then it should Just Work. You can verify this by viewing the Network tab in DevTools, and observe payloads occasionally being sent to `bam.nr-data.net`

## Related

- [Error monitoring research](https://lwd.atlassian.net/wiki/spaces/DD/pages/229835319/Error+Monitoring+Research)
