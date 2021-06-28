import User, { UserLeaveAdministrator } from "../../src/models/User";
import EmployerClaim from "../../src/models/EmployerClaim";
import { MockEmployerClaimBuilder } from "../test-utils";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withEmployerClaim from "../../src/hoc/withEmployerClaim";

jest.mock("../../src/hooks/useAppLogic");

describe("withEmployerClaim", () => {
  const secondClaimAbsenceId = "NTN-222-ABS-01";
  const user = new User({
    user_id: "mock_user_id",
    consented_to_data_sharing: true,
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_dba: "Test Company",
        employer_fein: "1298391823",
        employer_id: "dda903f-f093f-ff900",
        has_verification_data: true,
        verified: true,
      }),
      new UserLeaveAdministrator({
        employer_dba: "Tomato Touchdown",
        employer_fein: "**-***7192",
        employer_id: "io19fj9-00jjf-uiw3r",
        has_verification_data: false,
        verified: false,
      }),
    ],
  });
  const absence_id = "NTN-111-ABS-01";
  const PageComponent = () => <div />;
  const WrappedComponent = withEmployerClaim(PageComponent);
  let appLogic, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  function render(appLogic, absenceId = absence_id) {
    act(() => {
      wrapper = mount(
        <WrappedComponent
          appLogic={appLogic}
          query={{ absence_id: absenceId }}
        />
      );
    });
  }

  it("shows spinner when claim is not loaded", () => {
    appLogic.users.user = user;

    render(appLogic);

    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper.find("PageComponent").exists()).toBe(false);
  });

  it("loads the claim", () => {
    render(appLogic);

    expect(appLogic.employers.loadClaim).toHaveBeenCalledTimes(1);
    expect(appLogic.employers.loadClaim).toHaveBeenCalledWith("NTN-111-ABS-01");
  });

  it("loads the claim if the loaded claim is different", () => {
    render(appLogic, secondClaimAbsenceId);

    expect(appLogic.employers.loadClaim).toHaveBeenCalledTimes(1);
    expect(appLogic.employers.loadClaim).toHaveBeenCalledWith(
      secondClaimAbsenceId
    );
  });

  it("does not load the claim if it's already loaded", () => {
    appLogic.employers.claim = new EmployerClaim({
      fineos_absence_id: secondClaimAbsenceId,
    });

    render(appLogic, secondClaimAbsenceId);

    expect(appLogic.employers.loadClaim).not.toHaveBeenCalled();
  });

  it("does not load claim if user has not yet loaded", () => {
    appLogic.users.user = null;

    render(appLogic);
    wrapper.update();

    expect(appLogic.employers.loadClaim).not.toHaveBeenCalled();
  });

  describe("when claim is loaded", () => {
    let claim;

    beforeEach(() => {
      claim = new MockEmployerClaimBuilder().completed().create();
      appLogic.employers.claim = claim;
    });

    it("passes the 'user' prop from the withUser HOC", () => {
      appLogic.users.user = user;
      render(appLogic);

      expect(wrapper.find("PageComponent").prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claim' prop on the passed component", () => {
      appLogic.users.user = user;
      render(appLogic);

      expect(wrapper.find("PageComponent").prop("claim")).toBeInstanceOf(
        EmployerClaim
      );
      expect(wrapper.find("PageComponent").prop("claim")).toEqual(claim);
    });

    it("renders the wrapper component", () => {
      appLogic.users.user = user;
      render(appLogic);

      expect(wrapper.find("PageComponent").exists()).toBe(true);
      expect(wrapper.find("Spinner").exists()).toBe(false);
    });
  });

  describe("when user has verifiable employer", () => {
    let claim;

    beforeEach(() => {
      claim = new MockEmployerClaimBuilder().completed().create();
      appLogic.employers.claim = claim;
      appLogic.portalFlow.pathWithParams = "test-route";
    });

    it("redirects to Verify Contributions page if employer id matches", () => {
      render(appLogic);

      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        "/employers/organizations/verify-contributions",
        {
          employer_id: "dda903f-f093f-ff900",
          next: "test-route",
        }
      );
    });

    it("does not redirect to Verify Contributions page if employer is verified", () => {
      appLogic.users.user = user;

      render(appLogic);

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });

    it("does not redirect to Verify Contributions page if employer id does not match", () => {
      const unverifiedUserWithVerificationData = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Test Company",
            employer_fein: "1298391823",
            employer_id: "different_id",
            has_verification_data: true,
            verified: false,
          }),
        ],
      });
      appLogic.users.user = unverifiedUserWithVerificationData;

      render(appLogic);

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });
  });

  describe("when user has employer that cannot be verified", () => {
    let claim;

    beforeEach(() => {
      claim = new MockEmployerClaimBuilder()
        .completed()
        .employer_id("io19fj9-00jjf-uiw3r")
        .create();
      appLogic.employers.claim = claim;
      appLogic.portalFlow.pathWithParams = "test-route";
    });

    it("redirects to Cannot Verify page if employer id matches", () => {
      render(appLogic);

      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        "/employers/organizations/cannot-verify",
        {
          employer_id: "io19fj9-00jjf-uiw3r",
        }
      );
    });

    it("does not redirect to Cannot Verify page if employer id does not match", () => {
      const unverifiedUserWithoutVerificationData = new User({
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_id: "different_id",
            has_verification_data: false,
            verified: false,
          }),
        ],
      });
      appLogic.users.user = unverifiedUserWithoutVerificationData;

      render(appLogic);

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });
  });
});
