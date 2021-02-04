import { renderWithAppLogic, testHook } from "../../test-utils";
import Organizations from "../../../src/pages/employers/organizations";
import React from "react";
import { UserLeaveAdministrator } from "../../../src/models/User";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Organizations", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    process.env.featureFlags = { employerShowVerificationPages: false };
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Organizations appLogic={appLogic} />).dive();
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("shows the correct empty state", () => {
    ({ wrapper } = renderWithAppLogic(Organizations, {
      diveLevels: 1,
    }));

    expect(wrapper.find("LeaveAdministratorRow").exists()).toBe(false);
  });

  it("displays a table row for each user leave administrator", () => {
    const rows = wrapper.find("LeaveAdministratorRow");
    const titles = rows.map((row) => row.dive().find("span").first().text());
    const eins = rows.map((row) => row.dive().find("td").text());
    expect(titles).toEqual(["Book Bindings 'R Us", "Knitting Castle"]);
    expect(eins).toEqual(["1298391823", "390293443"]);
  });

  it('shows the "Verification required" tag if not verified', () => {
    const row = wrapper.find("LeaveAdministratorRow").first();
    const verificationTag = row.dive().find("Tag");
    expect(verificationTag.prop("label")).toBe("Verification required");
    expect(verificationTag.prop("state")).toBe("warning");
  });

  it('does not show the "Verification required" tag if already verified', () => {
    const row = wrapper.find("LeaveAdministratorRow").last();
    expect(row.dive().find("Tag").exists()).toBe(false);
  });

  describe('when "employerShowVerificationPages" feature flag is enabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowVerificationPages: true };
    });

    it("shows an Alert telling the user to start verification if there are unverified employers", () => {
      wrapper = shallow(<Organizations appLogic={appLogic} />).dive();
      expect(wrapper.find("Alert").exists()).toBe(true);
    });

    it("does not show an alert if all users are verified", () => {
      appLogic.users.user.user_leave_administrators = [
        new UserLeaveAdministrator({
          employer_dba: "Book Bindings 'R Us",
          employer_fein: "1298391823",
          employer_id: "dda903f-f093f-ff900",
          verified: true,
        }),
        new UserLeaveAdministrator({
          employer_dba: "Knitting Castle",
          employer_fein: "390293443",
          employer_id: "dda930f-93jfk-iej08",
          verified: true,
        }),
      ];
      wrapper = shallow(<Organizations appLogic={appLogic} />).dive();

      expect(wrapper.find("Alert").exists()).toBe(false);
    });
  });

  describe('when "employerShowVerificationPages" feature flag is disabled', () => {
    it("does not show an Alert telling the user to start verification if there are unverified employers", () => {
      wrapper = shallow(<Organizations appLogic={appLogic} />).dive();
      expect(wrapper.find("Alert").exists()).toBe(false);
    });

    it("does not show an alert if all users are verified", () => {
      appLogic.users.user.user_leave_administrators = [
        new UserLeaveAdministrator({
          employer_dba: "Book Bindings 'R Us",
          employer_fein: "1298391823",
          employer_id: "dda903f-f093f-ff900",
          verified: true,
        }),
        new UserLeaveAdministrator({
          employer_dba: "Knitting Castle",
          employer_fein: "390293443",
          employer_id: "dda930f-93jfk-iej08",
          verified: true,
        }),
      ];
      wrapper = shallow(<Organizations appLogic={appLogic} />).dive();

      expect(wrapper.find("Alert").exists()).toBe(false);
    });
  });
});
