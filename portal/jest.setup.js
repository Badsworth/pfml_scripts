/**
 * @file Sets up the testing framework for each test file
 * @see https://jestjs.io/docs/en/configuration#setupfilesafterenv-array
 */

// Setup I18n globally for tests, so English strings are displayed in rendered components
import "./src/locales/i18n";
import Adapter from "enzyme-adapter-react-16";
import Enzyme from "enzyme";

Enzyme.configure({ adapter: new Adapter() });

process.env.featureFlags = {};
