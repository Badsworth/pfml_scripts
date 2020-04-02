const path = require("path");

const buildEnv = process.env.BUILD_ENV || "dev";
const envVariables = require("./../infra/portal/config/" + buildEnv);

module.exports = {
  env: {
    ...envVariables,
  },
  exportTrailingSlash: true,
  experimental: {
    sassOptions: {
      includePaths: [
        path.resolve(__dirname, "node_modules/uswds/dist/scss"),
        path.resolve(__dirname, "node_modules"),
      ],
    },
  },
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
