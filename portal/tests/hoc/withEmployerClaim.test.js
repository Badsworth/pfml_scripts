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
  const userWithVerifiedEmployer = new User({
    user_id: "mock_user_id",
    consented_to_data_sharing: true,
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_dba: "Test Company",
        employer_fein: "1298391823",
        employer_id: "dda903f-f093f-ff900",
        verified: true,
      }),
    ],
  });
  const absence_id = "mock-absence-id";
  const PageComponent = () => <div />;
  const WrappedComponent = withEmployerClaim(PageComponent);
  let appLogic, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  function render(appLogic) {
    act(() => {
      wrapper = mount(
        <WrappedComponent appLogic={appLogic} query={{ absence_id }} />
      );
    });
  }

  it("shows spinner when claim is not loaded", () => {
    appLogic.users.user = userWithVerifiedEmployer;

    render(appLogic);

    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper.find("PageComponent").exists()).toBe(false);
  });

  it("loads the claim", () => {
    render(appLogic);

    expect(appLogic.employers.loadClaim).toHaveBeenCalledTimes(1);
    expect(appLogic.employers.loadClaim).toHaveBeenCalledWith(
      "mock-absence-id"
    );
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
      appLogic.users.user = userWithVerifiedEmployer;
      render(appLogic);

      expect(wrapper.find("PageComponent").prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claim' prop on the passed component", () => {
      appLogic.users.user = userWithVerifiedEmployer;
      render(appLogic);

      expect(wrapper.find("PageComponent").prop("claim")).toBeInstanceOf(
        EmployerClaim
      );
      expect(wrapper.find("PageComponent").prop("claim")).toEqual(claim);
    });

    it("renders the wrapper component", () => {
      appLogic.users.user = userWithVerifiedEmployer;
      render(appLogic);

      expect(wrapper.find("PageComponent").exists()).toBe(true);
      expect(wrapper.find("Spinner").exists()).toBe(false);
    });
  });

  describe("when user has unverified employer", () => {
    let claim;

    beforeEach(() => {
      claim = new MockEmployerClaimBuilder().completed().create();
      appLogic.employers.claim = claim;
      appLogic.portalFlow.pathWithParams = "test-route";
    });

    it("redirects to Verify Business page if employer id matches", () => {
      render(appLogic);

      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        "/employers/verify-business",
        {
          employer_id: "dda903f-f093f-ff900",
          next: "test-route",
        }
      );
    });

    it("does not redirect to Verify Business page if employer is verified", () => {
      appLogic.users.user = userWithVerifiedEmployer;

      render(appLogic);

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });

    it("does not redirect to Verify Business page if employer id does not match", () => {
      const userWithUnverifiedDiffEmployer = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Test Company",
            employer_fein: "1298391823",
            employer_id: "different_id",
            verified: false,
          }),
        ],
      });
      appLogic.users.user = userWithUnverifiedDiffEmployer;

      render(appLogic);

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });
  });
});
