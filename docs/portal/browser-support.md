# Browser support

Portal aims to support all modern browsers (Edge, Firefox, Chrome, Safari, Opera, et al). Portal also aims to support Internet Explorer 11. Portal does _not_ support Internet Explorer version 10 or below.

[Read more about this in Confluence](https://lwd.atlassian.net/l/c/NXf94Xf1).

[Read more about Next.js browser support here](https://nextjs.org/docs/basic-features/supported-browsers-features).

## Things to be aware of

- A `browserslist` file informs our CSS build process which browsers we support. [Learn more](https://nextjs.org/docs/advanced-features/customizing-postcss-config#customizing-target-browsers).
- Next.js automatically injects polyfills required for IE11 compatibility of our source code, however can't do this for any NPM dependencies that lack IE 11 compatibility. As a result, we have some manual polyfills in `src/polyfills.js`
- For all users of Internet Explorer, we display a banner at the top of the site to communicate their browser is not fully supported. See `UnsupportedBrowserBanner.js`

## Manual testing in Internet Explorer

To test the Portal locally using Internet Explorer 11 in BrowserStack or Sauce Labs, you will need to temporarily disable Amplify's cookie storage config setting in `_app.js` by commenting out the `cookieStorage` object. To test in IE 10 or below, you will need to build and export the static site:

```
$ npm build
$ npm start
```

These requirements are unique to local development.
