import Dashboard from "../../../src/pages/employers/dashboard";
import React from "react";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Employer dashboard", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  describe('when "employerShowDashboard" is enabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowDashboard: true };
      wrapper = shallow(<Dashboard appLogic={appLogic} />).dive();
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });
  });

  describe('when "employerShowDashboard" is disabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowDashboard: false };
    });

    it("redirects to the Welcome page", () => {
      wrapper = shallow(<Dashboard appLogic={appLogic} />).dive();
      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        routes.employers.welcome
      );
    });
  });
});
