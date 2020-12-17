/**
 * @file Jest CLI options for unit tests
 * @see https://jestjs.io/docs/en/cli
 */
module.exports = {
  clearMocks: true,
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "<rootDir>/tests/lib/",
    "<rootDir>/tests/test-utils.js",
  ],
  coverageReporters: ["text"],
  moduleFileExtensions: ["js", "mjs", "json", "jsx", "ts", "tsx", "node"],
  moduleNameMapper: {
    "\\.(png|svg)$": "<rootDir>/__mocks__/fileMock.js",
    "\\.(css|scss)$": "<rootDir>/__mocks__/styleMock.js",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  snapshotSerializers: ["enzyme-to-json/serializer"],
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "<rootDir>/config",
    "<rootDir>/tests/lib/",
    "<rootDir>/tests/test-utils.js",
  ],
  testRegex: "(/tests/.*|(\\.|/)(test|spec))\\.[jt]sx?$",
  coverageThreshold: {
    // TODO (CP-1509): Increase threshold to 90%
    global: {
      branches: 85,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};
