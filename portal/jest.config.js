/**
 * @file Jest CLI options
 * @see https://jestjs.io/docs/en/cli
 */
module.exports = {
  coverageReporters: ["text"],
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  snapshotSerializers: ["enzyme-to-json/serializer"],
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"]
};
