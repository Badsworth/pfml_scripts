/**
 * @file Sets up the testing framework for each test file
 * @see https://jestjs.io/docs/en/configuration#setupfilesafterenv-array
 */

import "@testing-library/jest-dom";
import { format } from "util";
// Setup I18n globally for tests, so English strings are displayed in rendered components
import { initializeI18n } from "./src/locales/i18n";
initializeI18n();

jest.mock("@aws-amplify/auth");

/**
 * Mock environment variables
 */
process.env.apiUrl = "http://localhost/jest-mock-api";
process.env.awsConfig = {};
process.env.buildEnv = "mock-build-env";
process.env.domain = "localhost";
process.env.featureFlags = {};
process.env.newRelicAppId = "mock-new-relic-id";
process.env.gtmConfig = { auth: "mock-gtm-auth", preview: "mock-env" };
process.env.session = { secondsOfInactivityUntilLogout: 10 };

/**
 * Mock DOM APIs
 */
global.fetch = jest.fn();
global.scrollTo = jest.fn();
// https://github.com/jsdom/jsdom/issues/1695
Element.prototype.scrollIntoView = jest.fn();

// URL.createObjectURL() hasn't been implemented in the jest DOM yet but will be
// eventually. When it is (and this error triggers) we should remove this mock.
// Read more: https://github.com/jsdom/jsdom/issues/1721
if (URL.createObjectURL) {
  throw new Error(
    "jest DOM has added URL.createObjectURL() -- we can remove this hack now"
  );
}
URL.createObjectURL = () => "image.png";
URL.revokeObjectURL = jest.fn();

/**
 * Mock global libraries
 */
global.newrelic = {
  addPageAction: jest.fn(),
  noticeError: jest.fn(),
  setCurrentRouteName: jest.fn(),
};

/**
 * Cleanup & setup
 */
const initialProcessEnv = Object.assign({}, process.env);

beforeEach(() => {
  // Require each test to run an assertion. This is often useful in catching
  // async test logic bugs
  expect.hasAssertions();
  // Reset our environment variables before each test run
  process.env = { ...initialProcessEnv };
  jest.spyOn(console, "error").mockImplementation((msg, ...args) => {
    throw new Error(format(`console.error: ${msg}`, ...args));
  });
  jest.spyOn(console, "warn").mockImplementation((msg, ...args) => {
    throw new Error(format(`console.warning: ${msg}`, ...args));
  });
});
