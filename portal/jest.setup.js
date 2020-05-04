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

// Mock the API URL to make sure requests don't actually go anywhere
process.env.apiUrl = "http://localhost/jest-mock-api";

process.env.featureFlags = {};

// Reset our environment variables before each test run
const currentProcessEnv = process.env;
beforeEach(() => {
  process.env = currentProcessEnv;
});
