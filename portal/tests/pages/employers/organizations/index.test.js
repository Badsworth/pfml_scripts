import { renderWithAppLogic, testHook } from "../../../test-utils";
import Index from "../../../../src/pages/employers/organizations";
import React from "react";
import { UserLeaveAdministrator } from "../../../../src/models/User";
import routeWithParams from "../../../../src/utils/routeWithParams";
import routes from "../../../../src/routes";
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
    process.env.featureFlags = {
      employerShowAddOrganization: false,
      employerShowVerifications: false,
    };
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
    expect(titles).toEqual([
      "Book Bindings 'R Us",
      "Knitting Castle",
      "Tomato Touchdown",
    ]);
    expect(eins).toEqual(["**-***1823", "**-***3443", "**-***7192"]);
  });

  describe('when "employerShowAddOrganization" feature flag is enabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowAddOrganization: true };
      wrapper = shallow(<Index appLogic={appLogic} />).dive();
    });

    it("shows the correct future availability statement", () => {
      const futureAvaiabilityMessage = wrapper.find(
        '[data-test="future-availability-message"]'
      );
      expect(futureAvaiabilityMessage.text()).toContain(
        "You can manage leave for these organizations."
      );
    });

    it("displays a button linked to Add Organization page", () => {
      const button = wrapper.find("ButtonLink");
      expect(button.exists()).toBe(true);
      expect(button.prop("href")).toBe(routes.employers.addOrganization);
    });
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
          has_verification_data: true,
          verified: true,
        }),
      ];
      wrapper = shallow(<Index appLogic={appLogic} />).dive();

      expect(wrapper.find("Alert").exists()).toBe(false);
    });

    describe("for orgs that are not verified", () => {
      describe("and can be verified", () => {
        const expectedUrl = routeWithParams("employers.verifyContributions", {
          employer_id: "dda903f-f093f-ff900",
          next: "/employers/organizations",
        });
        let row;

        beforeEach(() => {
          renderPage();
          row = wrapper.find("LeaveAdministratorRow").first().dive();
        });

        it('shows the "Verification required" tag', () => {
          const verificationTag = row.find("Tag");
          expect(verificationTag.parent().is("a")).toBe(true);
          expect(verificationTag.parent().prop("href")).toBe(expectedUrl);
          expect(verificationTag.prop("label")).toBe("Verification required");
          expect(verificationTag.prop("state")).toBe("warning");
        });

        it("links to the correct Verify Business page", () => {
          const link = row.find("a").first();
          expect(link.text()).toBe("Book Bindings 'R Us");
          expect(link.prop("href")).toBe(expectedUrl);
        });
      });

      describe("and canNOT be verified", () => {
        const expectedUrl = routeWithParams("employers.cannotVerify", {
          employer_id: "io19fj9-00jjf-uiw3r",
        });
        let row;

        beforeEach(() => {
          renderPage();
          row = wrapper.find("LeaveAdministratorRow").at(2).dive();
        });

        it('shows the "Verification blocked" tag', () => {
          const verificationTag = row.find("Tag");
          expect(verificationTag.parent().is("a")).toBe(true);
          expect(verificationTag.parent().prop("href")).toBe(expectedUrl);
          expect(verificationTag.prop("label")).toBe("Verification blocked");
          expect(verificationTag.prop("state")).toBe("error");
        });

        it("links to the Cannot Verify page", () => {
          const link = row.find("a").first();
          expect(link.text()).toBe("Tomato Touchdown");
          expect(link.prop("href")).toBe(expectedUrl);
        });
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

      it("does not link anywhere", () => {
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
      let verificationBlockedRow, verificationRequiredRow, verifiedRow;
      beforeEach(() => {
        renderPage();
        verificationRequiredRow = wrapper
          .find("LeaveAdministratorRow")
          .first()
          .dive();
        verifiedRow = wrapper.find("LeaveAdministratorRow").at(1).dive();
        verificationBlockedRow = wrapper
          .find("LeaveAdministratorRow")
          .at(2)
          .dive();
      });

      it('does not show the "Verification required" tag', () => {
        expect(verificationRequiredRow.find("Tag").exists()).toBe(false);
        expect(verifiedRow.find("Tag").exists()).toBe(false);
        expect(verificationBlockedRow.find("Tag").exists()).toBe(false);
      });

      it("does not navigate anywhere on click", () => {
        expect(verificationRequiredRow.find("a").exists()).toBe(false);
        expect(verifiedRow.find("a").exists()).toBe(false);
        expect(verificationBlockedRow.find("a").exists()).toBe(false);
      });
    });
  });
});
