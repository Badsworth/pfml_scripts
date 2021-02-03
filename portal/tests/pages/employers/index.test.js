import Index from "../../../src/pages/employers";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Employer index", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    process.env.featureFlags = {};
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Index appLogic={appLogic} />).dive();
  });

  it("renders page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays coming soon banner when employerShowNewsBanner is true", () => {
    process.env.featureFlags = { employerShowNewsBanner: true };
    wrapper = shallow(<Index appLogic={appLogic} />).dive();

    expect(wrapper.find("NewsBanner").exists()).toEqual(true);
  });

  it("displays links to Organizations page when employerShowVerifications is true", () => {
    process.env.featureFlags = { employerShowVerifications: true };
    wrapper = shallow(<Index appLogic={appLogic} />).dive();

    expect(wrapper.find("Alert").exists()).toEqual(true);
    wrapper
      .find("aside")
      .find("Heading")
      .forEach((heading) => expect(heading.dive()).toMatchSnapshot());
    wrapper
      .find("aside")
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });
});
