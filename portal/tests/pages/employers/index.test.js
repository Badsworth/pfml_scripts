import Index from "../../../src/pages/employers/index";
import Link from "next/link";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Index appLogic={appLogic} />).dive();
  });

  it("renders dashboard content", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("displays Link component with review claim", () => {
    expect(wrapper.find(Link).render().text()).toEqual("Review claim");
  });
});
