/**
 * @file Jest CLI options for unit tests
 * @see https://jestjs.io/docs/en/cli
 */
module.exports = {
  clearMocks: true,
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "<rootDir>/tests-old/test-utils/",
    "<rootDir>/tests/lib/",
    "<rootDir>/tests/test-utils/",
  ],
  coverageReporters: ["text"],
  moduleFileExtensions: ["js", "mjs", "json", "jsx", "ts", "tsx", "node"],
  moduleNameMapper: {
    "\\.(png|svg)$": "<rootDir>/__mocks__/fileMock.js",
    "\\.(css|scss)$": "<rootDir>/__mocks__/styleMock.js",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  snapshotSerializers: ["enzyme-to-json/serializer"],
  testEnvironment: "jsdom",
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "<rootDir>/config",
    "<rootDir>/tests-old/test-utils/",
    "<rootDir>/tests/lib/",
    "<rootDir>/tests/test-utils/",
  ],
  testRegex: "(/(tests-old|tests)/.*|(\\.|/)(test|spec))\\.[jt]sx?$",
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};
