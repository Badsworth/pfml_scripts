/**
 * @file Sets up the testing framework for each test file
 * @see https://jestjs.io/docs/en/configuration#setupfilesafterenv-array
 */
import Adapter from "enzyme-adapter-react-16";
import Enzyme from "enzyme";

Enzyme.configure({ adapter: new Adapter() });
