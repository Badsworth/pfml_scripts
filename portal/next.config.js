// @ts-check - This file has to be a .js file since it's not ran through a transpiler.
const mayflowerAssets = require("@massds/mayflower-assets");
const buildEnv = process.env.BUILD_ENV || "development";
const releaseVersion = process.env.releaseVersion
  ? `massgov-pfml-portal@${process.env.releaseVersion.replace("portal/", "")}`
  : "";
const envVariables = require("./config")[buildEnv] || {};
const featureFlags = require("./config/featureFlags")(buildEnv);
// @ts-expect-error Typing for this module isn't super important for our purposes:
const withImages = require("next-images");
// @ts-expect-error Typing for this module isn't super important for our purposes:
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE_BUNDLE === "true",
});
const withTranspileModules = require("next-transpile-modules");

// eslint-disable-next-line no-console
console.log(`📦 Using "${buildEnv}" environment variables to build the site.`);

/**
 * @type {import('next').NextConfig}
 */
const config = {
  // In our code, we can reference environment variables from process.env
  // https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  env: {
    ...envVariables,
    featureFlags,
    buildEnv,
    releaseVersion,
  },
  // Output source maps for production builds so they can aid in debugging production issues
  productionBrowserSourceMaps: true,
  sassOptions: {
    // Mayflowers requires us to expose its includePaths so its imports work
    includePaths: mayflowerAssets.includePaths,
  },
  images: {
    disableStaticImages: true,
  },
  trailingSlash: true,
  webpack: function (webpackConfig) {
    // Include our polyfills before all other code
    // See: https://github.com/zeit/next.js/tree/master/examples/with-polyfills
    const originalEntry = webpackConfig.entry;

    webpackConfig.entry = async () => {
      const entries = await originalEntry();
      const mainEntryFilename = "main.js";
      const polyfillsPath = "./src/polyfills.ts";

      if (
        entries[mainEntryFilename] &&
        !entries[mainEntryFilename].includes(polyfillsPath)
      ) {
        entries[mainEntryFilename].unshift(polyfillsPath);
      }

      return entries;
    };

    return webpackConfig;
  },
};

/**
 * @type {import('next').NextConfig}
 */
module.exports = withBundleAnalyzer(
  // We transpile Mayflower and USWDS since there's an issue that results in untranspiled
  // modules being included in our code, which breaks IE11 compatibility
  // https://jira.mass.gov/browse/DP-20446
  withTranspileModules(["@massds/mayflower-react", "uswds"])(withImages(config))
);
