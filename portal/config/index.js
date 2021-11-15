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
  training: merge({}, defaultEnvVariables, require("./training")),
  performance: merge({}, defaultEnvVariables, require("./performance")),
  uat: merge({}, defaultEnvVariables, require("./uat")),
  breakfix: merge({}, defaultEnvVariables, require("./breakfix")),
  "cps-preview": merge({}, defaultEnvVariables, require("./cps-preview")),
};
