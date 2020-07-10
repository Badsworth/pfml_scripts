/**
 * @file Sets up the testing framework for each test file
 * @see https://jestjs.io/docs/en/configuration#setupfilesafterenv-array
 */

import Adapter from "enzyme-adapter-react-16";
import Enzyme from "enzyme";
// Setup I18n globally for tests, so English strings are displayed in rendered components
import { initializeI18n } from "./src/locales/i18n";
initializeI18n();

Enzyme.configure({ adapter: new Adapter() });

/**
 * Mock environment variables
 */
process.env.apiUrl = "http://localhost/jest-mock-api";
process.env.featureFlags = {};
process.env.newRelicAppId = "mock-new-relic-id";
process.env.gtmConfig = { auth: "mock-gtm-auth", preview: "mock-env" };

/**
 * Mock DOM APIs
 */
global.fetch = jest.fn();
global.scrollTo = jest.fn();

/**
 * Mock global libraries
 */
global.newrelic = {
  noticeError: jest.fn(),
  setCurrentRouteName: jest.fn(),
};

/**
 * Cleanup & setup
 */
const initialProcessEnv = Object.assign({}, process.env);

beforeEach(() => {
  // Reset our environment variables before each test run
  process.env = initialProcessEnv;
});
