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

  it("renders caring leave form link when showCaringLeaveType is true", () => {
    // TODO (CP-2311): Remove showCaringLeaveType flag once caring leave is made available in Production
    process.env.featureFlags = { showCaringLeaveType: true };
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();
    expect(
      wrapper
        .find(`Trans[i18nKey="pages.employersWelcome.viewFormsBody"]`)
        .dive()
    ).toMatchSnapshot();
  });

  it("renders caring leave alert when showCaringLeaveType is true", () => {
    process.env.featureFlags = {
      showCaringLeaveType: true,
    };
    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();

    expect(wrapper.find("Alert").exists()).toEqual(true);

    expect(
      wrapper
        .find(
          `Trans[i18nKey="pages.employersWelcome.caringLeaveInfoAlertBody"]`
        )
        .dive()
    ).toMatchSnapshot();
  });

  it("renders other leave alert when claimantShowOtherLeaveStep is true", () => {
    process.env.featureFlags = {
      claimantShowOtherLeaveStep: true,
    };
    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();

    expect(wrapper.find("Alert").exists()).toEqual(true);

    expect(
      wrapper
        .find(`Trans[i18nKey="pages.employersWelcome.otherLeaveInfoAlertBody"]`)
        .dive()
    ).toMatchSnapshot();
  });

  it("does not render caring leave alert when showCaringLeaveType is true AND claimantShowOtherLeaveStep is true", () => {
    process.env.featureFlags = {
      showCaringLeaveType: true,
      claimantShowOtherLeaveStep: true,
    };
    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();

    expect(
      wrapper
        .find(
          `Trans[i18nKey="pages.employersWelcome.caringLeaveInfoAlertBody"]`
        )
        .exists()
    ).toEqual(false);
  });
});
