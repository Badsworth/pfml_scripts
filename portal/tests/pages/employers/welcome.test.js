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

  describe("when employerShowDashboard is false", () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowDashboard: false };
      testHook(() => {
        appLogic = useAppLogic();
      });

      wrapper = shallow(<Welcome appLogic={appLogic} />).dive();
    });

    it("does not show the navigation bar", () => {
      expect(wrapper.find("EmployerNavigationTabs").exists()).toBe(false);
    });

    it("does not show the View Applications list item", () => {
      const viewApplicationsTitle = wrapper.find('Heading[level="2"]').first();
      expect(viewApplicationsTitle.dive().text()).not.toContain(
        "View all applications"
      );
    });
  });

  describe("when employerShowDashboard is true", () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowDashboard: true };
      testHook(() => {
        appLogic = useAppLogic();
      });

      wrapper = shallow(<Welcome appLogic={appLogic} />).dive();
    });

    it("shows the navigation bar", () => {
      expect(wrapper.find("EmployerNavigationTabs").exists()).toBe(true);
    });

    it("shows the View Applications list item", () => {
      const viewApplicationsTitle = wrapper.find('Heading[level="2"]').first();
      expect(viewApplicationsTitle.dive().text()).toContain(
        "View all applications"
      );
    });
  });

  it("displays banner when employerShowNewsBanner is true", () => {
    process.env.featureFlags = { employerShowNewsBanner: true };
    wrapper = shallow(<Welcome appLogic={appLogic} />).dive();

    expect(wrapper.find("NewsBanner").exists()).toEqual(true);
  });

  it("displays links to Organizations page when employerShowVerifications is true", () => {
    process.env.featureFlags = { employerShowVerifications: true };
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
});
