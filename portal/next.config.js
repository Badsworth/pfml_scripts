const mayflowerAssets = require("@massds/mayflower-assets");
const buildEnv = process.env.BUILD_ENV || "development";
const envVariables = require("./config")[buildEnv];
const featureFlags = require("./config/featureFlags")(buildEnv);
const withImages = require("next-images");
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE_BUNDLE === "true",
});
// TODO: Next.js will eventually provide production source maps out of the box,
// so remove this plugin when that becomes available. Experimental support was
// added in https://github.com/zeit/next.js/pull/13018
const withSourceMaps = require("@zeit/next-source-maps");

// eslint-disable-next-line no-console
console.log(`📦 Using "${buildEnv}" environment variables to build the site.`);

const config = {
  // In our code, we can reference environment variables from process.env
  // https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  env: {
    ...envVariables,
    featureFlags,
  },
  sassOptions: {
    // Mayflowers requires us to expose its includePaths so its imports work
    includePaths: mayflowerAssets.includePaths,
  },
  trailingSlash: true,
  webpack: function (webpackConfig) {
    // Include our polyfills before all other code
    // See: https://github.com/zeit/next.js/tree/master/examples/with-polyfills
    const originalEntry = webpackConfig.entry;

    webpackConfig.entry = async () => {
      const entries = await originalEntry();
      const mainEntryFilename = "main.js";
      const polyfillsPath = "./src/polyfills.js";

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

module.exports = withBundleAnalyzer(withSourceMaps(withImages(config)));
