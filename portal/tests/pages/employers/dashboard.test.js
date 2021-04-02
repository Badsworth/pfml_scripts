import User, { UserLeaveAdministrator } from "../../../src/models/User";
import { mount, shallow } from "enzyme";
import Dashboard from "../../../src/pages/employers/dashboard";
import React from "react";
import { act } from "react-dom/test-utils";
import routes from "../../../src/routes";
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
      wrapper
        .find("Trans")
        .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
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

  describe('when "employerShowVerifications" is also enabled', () => {
    beforeEach(() => {
      process.env.featureFlags = {
        employerShowDashboard: true,
        employerShowVerifications: true,
      };
      appLogic.users.user = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Book Bindings 'R Us",
            employer_fein: "**-***1823",
            employer_id: "dda903f-f093f-ff900",
            has_verification_data: true,
            verified: false,
          }),
        ],
      });
      act(() => {
        wrapper = mount(<Dashboard appLogic={appLogic} />);
      });
    });

    it("renders the banner if there are any unverified employers", () => {
      expect(wrapper.find("Alert").exists()).toEqual(true);
    });

    it("renders instructions if there are no verified employers", () => {
      expect(wrapper.find("Trans")).toHaveLength(2);
      wrapper.find("Trans").forEach((trans) => expect(trans).toMatchSnapshot());
    });
  });
});
