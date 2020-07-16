const defaultEnvVariables = require("./default");
const { merge } = require("lodash");

/**
 * Dictionary of environment configs
 */
module.exports = {
  development: merge({}, defaultEnvVariables, require("./development")),
  test: merge({}, defaultEnvVariables, require("./test")),
  stage: merge({}, defaultEnvVariables, require("./stage")),
  prod: merge({}, defaultEnvVariables, require("./prod")),
};
