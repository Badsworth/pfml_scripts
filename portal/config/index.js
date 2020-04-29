/**
 * Dictionary of environment configs
 */
module.exports = {
  development: require("./development"),
  test: require("./test"),
  stage: require("./stage"),
  prod: require("./prod"),
};
