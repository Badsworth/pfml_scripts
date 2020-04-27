const buildEnv = process.env.BUILD_ENV || "development";
const envVariables = require("./config")[buildEnv];
const featureFlags = require("./config/featureFlags")(buildEnv);

// eslint-disable-next-line no-console
console.log(`📦 Using "${buildEnv}" environment variables to build the site.`);

module.exports = {
  // In our code, we can reference environment variables from process.env
  // https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  env: {
    ...envVariables,
    featureFlags,
  },
  exportTrailingSlash: true,
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
