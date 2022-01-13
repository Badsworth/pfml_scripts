# Web Analytics

Massachusetts uses [Google Analytics](https://analytics.google.com/) for cross-domain tracking on mass.gov properties. This works by including [a Google Tag Manager JS snippet](https://developers.google.com/tag-manager/quickstart) in the document head. [Google Tag Manager](https://tagmanager.google.com/) is configured to dynamically insert Google Analytics onto the page when the web page is initially loaded.

## Viewing analytics

Analytics for all of our environments are visible in the "mass.gov cross domain tracking" Google Analytics property. From within this property, you can filter results by the environment's domain you're interested in seeing. For example, to view real time traffic for all `paidleave` environments, you can [visit this page](https://analytics.google.com/analytics/web/?authuser=1#/realtime/rt-content/a12471675w181800649p192039415/filter.list=10~~=paidleave;/).

## Custom metrics

Single-page Application page views and custom event tracking should be setup through [Google Tag Manager triggers](https://support.google.com/tagmanager/topic/7679108). Using the Google Analytics `ga` function isn't recommended when using Google Tag Manager.

## Environment Configuration

Each Portal environment should have a corresponding Google Tag Manager environment. Once a Google Tag Manager environment exists, we need to set the Portal `gtmConfigAuth` and `gtmConfigPreview` environment variables based on that Google Tag Manager environment's values. You can find these values through the Google Tag Manager website in the Admin section by navigating to the environment and looking at the JavaScript snippet for that environment. Look for a URL with `gtm_auth` and `gtm_preview` query parameters. The values for those query parameters should be set as the corresponding Portal environment variables.

### Content Security Policy

In order for the Google Tag Manager scripts and Google Analytics scripts to run, we need to make sure the [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) set by CloudFront in [cloudfront-handler.js](../../infra/portal/template/cloudfront-handler.js) allows:

- The inline Google Tag Manager scripts
- Scripts from https://www.googletagmanager.com/
- Scripts from https://www.google-analytics.com/
- Tracking images from https://www.google-analytics.com/

The inline scripts need to be allowed by computing a Base64 encoded SHA-256 hash of the inline script and adding the hash to the allowed script sources in the Content Security Policy. To compute a hash, you can use an online tool like [SHA256 Hash Generator](https://passwordsgenerator.net/sha256-hash-generator/). Or to use the Terminal, you can save the JavaScript snippet into a file e.g. `gtm-snippet` and run

```
$ cat gtm-snippet | openssl sha256 -binary | openssl base64
```

## Change Management

To make changes to Google Tag Manager, create a new Google Tag Manager version with the desired changes, and publish those changes to the Google Tag Manager Test environment.

To test those changes before publishing to Google Tag Manager's Stage and Prod environments, we need to be able to override the environment configuration to use the Google Tag Manager Test environment, which is something that will be implemented as part of [CP-645](https://lwd.atlassian.net/browse/CP-645). In the meantime, you can manually insert the Google Tag Manager Test environment snippet onto the page you're viewing by executing the following lines of code in the browser console. Note the `gtm_auth` and `gtm_preview` values below are for the Google Tag Manager Test environment.

```
var myScript = document.createElement('script');
myScript.textContent = "(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n" +
"new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n" +
"j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n" +
"'https://www.googletagmanager.com/gtm.js?id='+i+dl+ '&gtm_auth=SiSVu0U7VjoUiceaFWQeqA&gtm_preview=env-5&gtm_cookies_win=x';f.parentNode.insertBefore(j,f);\n" +
"})(window,document,'script','dataLayer','GTM-MCLNNQC');";
document.head.appendChild(myScript);
```

### Publishing a new GTM version

Once you've tested the changes in a Test environment, you can publish a new Google Tag Manager version to other environments. You can do this from the `Versions` tab, clicking the `...` icon, and then clicking "Publish to..."

### Account Set Up

In order to update Google Tag Manager configuration, you need a Google account associated with your @mass.gov email, and that account needs to be granted publish access in Google Tag Manager.

In order to view Google Analytics data, your @mass.gov Google account needs to be added as a user to the mass.gov Google Analytics account.

### Enabling Google Tag Manager and Google Analytics

If you have a browser extension installed to block trackers, you may need to safelist the google tag manager and google analytics. If it's not being blocked, then it should Just Work. You can verify this by viewing the Network tab in DevTools, and observe network requests to `googletagmanager.com` and `google-analytics.com`.

## Related

- [Web analytics research](https://lwd.atlassian.net/wiki/spaces/DD/pages/309953277/Web+Analytics+Research)
