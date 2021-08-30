import React from "react";
import Welcome from "../../../src/pages/employers/welcome";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Employer welcome", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    process.env.featureFlags = {};
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();
  });

  it("renders page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays links to Organizations page", () => {
    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();

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

  it("renders other leave alert", () => {
    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();

    expect(wrapper.find("Alert").exists()).toEqual(true);

    expect(
      wrapper
        .find(`Trans[i18nKey="pages.employersWelcome.otherLeaveInfoAlertBody"]`)
        .dive()
    ).toMatchSnapshot();
  });
});
