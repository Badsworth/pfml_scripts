import Index from "../../../src/pages/employers";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Employer index", () => {
  let appLogic;

  it("renders the page", () => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    const wrapper = shallow(<Index appLogic={appLogic} />);

    expect(wrapper.dive()).toMatchSnapshot();
  });
});
