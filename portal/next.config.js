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
};
