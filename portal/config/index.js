// @ts-check
const defaultEnvVariables = require("./default");
const { merge } = require("lodash");

/**
 * Dictionary of environment configs
 * @type {Record<string, Record<string, string>>}
 */
const environments = {
  development: merge({}, defaultEnvVariables, require("./development")),
  test: merge({}, defaultEnvVariables, require("./test")),
  stage: merge({}, defaultEnvVariables, require("./stage")),
  prod: merge({}, defaultEnvVariables, require("./prod")),
  training: merge({}, defaultEnvVariables, require("./training")),
  performance: merge({}, defaultEnvVariables, require("./performance")),
  uat: merge({}, defaultEnvVariables, require("./uat")),
  breakfix: merge({}, defaultEnvVariables, require("./breakfix")),
  "cps-preview": merge({}, defaultEnvVariables, require("./cps-preview")),
  long: merge({}, defaultEnvVariables, require("./long")),
  trn2: merge({}, defaultEnvVariables, require("./trn2")),
  "infra-test": merge({}, defaultEnvVariables, require("./infra-test")),
  local: merge({}, defaultEnvVariables, require("./local")),
};

module.exports = environments;
