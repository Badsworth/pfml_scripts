/**
 * @file Jest CLI options for unit tests
 * @see https://jestjs.io/docs/en/cli
 */
module.exports = {
  clearMocks: true,
  coveragePathIgnorePatterns: ["/node_modules/", "<rootDir>/tests/lib/"],
  coverageReporters: ["text"],
  moduleNameMapper: {
    "\\.(css|scss)$": "<rootDir>/__mocks__/styleMock.js",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  snapshotSerializers: ["enzyme-to-json/serializer"],
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "<rootDir>/config",
    "<rootDir>/tests/lib/",
    // Exclude E2E tests since those are part of a separate Jest config (jest-e2e.config.js)
    "<rootDir>/tests/end-to-end",
    "<rootDir>/tests/test-utils.js",
  ],
  testRegex: "(/tests/.*|(\\.|/)(test|spec))\\.[jt]sx?$",
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};
