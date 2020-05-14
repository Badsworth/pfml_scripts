/**
 * @file Jest CLI options for end-to-end tests specifically,
 * which run in a Puppeteer environment
 * @see https://jestjs.io/docs/en/cli
 */
module.exports = {
  clearMocks: true,
  preset: "jest-puppeteer",
  roots: ["<rootDir>/__tests__/end-to-end"],
  setupFilesAfterEnv: ["<rootDir>/jest-e2e.setup.js"],
};
