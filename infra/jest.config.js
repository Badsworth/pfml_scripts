/**
 * @file Jest CLI options
 * @see https://jestjs.io/docs/en/cli
 */
module.exports = {
  coverageReporters: ["text"],
  testPathIgnorePatterns: ["<rootDir>/node_modules/"],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};
