import Index from "../../src/pages/index";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    // Dive once since Index is wrapped by withUser
    wrapper = shallow(<Index appLogic={appLogic} />).dive();
  });

  it("renders dashboard content", () => {
    expect(wrapper).toMatchSnapshot();
  });
});
