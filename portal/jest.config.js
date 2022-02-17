/**
 * @file Jest CLI options for unit tests
 * @see https://jestjs.io/docs/en/cli
 * @see https://nextjs.org/docs/advanced-features/compiler#jest
 */
const nextJest = require("next/jest");

// Setting time zone explicitly so that we can run tests with a consistent timezone
// (jest test files don't have access to process.env early enough, so setting here)
// Alternately, we could set via the CLI: https://github.com/facebook/jest/issues/9856#issuecomment-776532082
process.env.TZ = "America/New_York";

const createJestConfig = nextJest({ dir: "./" });

// Any custom config you want to pass to Jest
const customJestConfig = {
  clearMocks: true,
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "<rootDir>/storybook/",
    "<rootDir>/tests/lib/",
    "<rootDir>/tests/test-utils/",
  ],
  coverageReporters: ["text"],
  moduleFileExtensions: ["js", "mjs", "json", "jsx", "ts", "tsx", "node"],
  moduleNameMapper: {
    // Support alias imports. Required for our Storybook tests, since our
    // Storybook files utilize alias imports.
    "^lib(.*)$": "<rootDir>/lib$1",
    "^src(.*)$": "<rootDir>/src$1",
    "^storybook(.*)$": "<rootDir>/storybook$1",
    "^tests(.*)$": "<rootDir>/tests$1",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  snapshotFormat: {
    printBasicPrototype: false,
  },
  testEnvironment: "jsdom",
  testRegex: "tests/.*test.[jt]sx?$",
  transformIgnorePatterns: [
    // Some assets are ECMAScript Modules, which need transformed
    // in our test environment. Those modules need listed here:
    // https://stackoverflow.com/questions/69075510/jest-tests-failing-on-d3-import
    "node_modules/(?!d3|d3-array|delaunator|entity-decode|internmap|mermaid|robust-predicates/)",
  ],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
