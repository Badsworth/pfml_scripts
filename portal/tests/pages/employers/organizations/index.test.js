import { renderWithAppLogic, testHook } from "../../../test-utils";
import Index from "../../../../src/pages/employers/organizations";
import React from "react";
import { UserLeaveAdministrator } from "../../../../src/models/User";
import routeWithParams from "../../../../src/utils/routeWithParams";
import { shallow } from "enzyme";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic, wrapper;

  const renderPage = () => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Index appLogic={appLogic} />).dive();
  };

  beforeEach(() => {
    process.env.featureFlags = { employerShowVerifications: false };
    renderPage();
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("shows the correct empty state", () => {
    ({ wrapper } = renderWithAppLogic(Index, {
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

  describe('when "employerShowVerifications" feature flag is enabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowVerifications: true };
    });

    it("shows an Alert telling the user to start verification if there are unverified employers", () => {
      wrapper = shallow(<Index appLogic={appLogic} />).dive();
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
      wrapper = shallow(<Index appLogic={appLogic} />).dive();

      expect(wrapper.find("Alert").exists()).toBe(false);
    });

    describe("for orgs that are not verified", () => {
      let row;
      beforeEach(() => {
        renderPage();
        row = wrapper.find("LeaveAdministratorRow").first().dive();
      });

      it('shows the "Verification required" tag', () => {
        const verificationTag = row.find("Tag");
        expect(verificationTag.prop("label")).toBe("Verification required");
        expect(verificationTag.prop("state")).toBe("warning");
      });

      it("links to the correct Verify Business page", () => {
        const link = row.find("a");
        expect(link.prop("href")).toBe(
          routeWithParams("employers.verifyContributions", {
            employer_id: "dda903f-f093f-ff900",
            next: "/employers/organizations",
          })
        );
      });
    });

    describe("for orgs that are verified", () => {
      let row;
      beforeEach(() => {
        row = wrapper.find("LeaveAdministratorRow").at(1).dive();
      });

      it('does not show the "Verification required" tag', () => {
        expect(row.find("Tag").exists()).toBe(false);
      });

      it("does not link to the Verify Contributions page", () => {
        expect(row.find("a").exists()).toBe(false);
      });
    });
  });

  describe('when "employerShowVerifications" feature flag is disabled', () => {
    it("does not show an Alert telling the user to start verification if there are unverified employers", () => {
      wrapper = shallow(<Index appLogic={appLogic} />).dive();
      expect(wrapper.find("Alert").exists()).toBe(false);
    });

    describe("for all orgs", () => {
      let notVerifiedRow, verifiedRow;
      beforeEach(() => {
        renderPage();
        notVerifiedRow = wrapper.find("LeaveAdministratorRow").first().dive();
        verifiedRow = wrapper.find("LeaveAdministratorRow").at(1).dive();
      });

      it('does not show the "Verification required" tag', () => {
        expect(notVerifiedRow.find("Tag").exists()).toBe(false);
        expect(verifiedRow.find("Tag").exists()).toBe(false);
      });

      it("does not navigate anywhere on click", () => {
        expect(notVerifiedRow.find("a").exists()).toBe(false);
        expect(verifiedRow.find("a").exists()).toBe(false);
      });
    });
  });
});
