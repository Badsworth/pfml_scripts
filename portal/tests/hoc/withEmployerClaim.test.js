import EmployerClaim from "../../src/models/EmployerClaim";
import { MockEmployerClaimBuilder } from "../test-utils";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withEmployerClaim from "../../src/hoc/withEmployerClaim";

jest.mock("../../src/hooks/useAppLogic");

describe("withEmployerClaim", () => {
  let absence_id, appLogic, wrapper;

  const PageComponent = () => <div />;
  const WrappedComponent = withEmployerClaim(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(
        <WrappedComponent appLogic={appLogic} query={{ absence_id }} />
      );
    });
  }

  beforeEach(() => {
    absence_id = "mock-absence-id";
    appLogic = useAppLogic();
  });

  it("Shows spinner when claim is not loaded", () => {
    render();

    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper.find("PageComponent").exists()).toBe(false);
  });

  it("loads the claim", () => {
    render();

    expect(appLogic.employers.load).toHaveBeenCalledTimes(1);
    expect(appLogic.employers.load).toHaveBeenCalledWith("mock-absence-id");
  });

  it("does not load claim if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;

    render();
    wrapper.update();

    expect(appLogic.employers.load).not.toHaveBeenCalled();
  });

  describe("when claim is loaded", () => {
    let claim;

    beforeEach(() => {
      claim = new MockEmployerClaimBuilder().completed().create();
      appLogic.employers.claim = claim;
    });

    it("passes through the 'user' prop from the withUser HOC", () => {
      render();

      expect(wrapper.find("PageComponent").prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claim' prop on the passed component", () => {
      render();

      expect(wrapper.find("PageComponent").prop("claim")).toBeInstanceOf(
        EmployerClaim
      );
      expect(wrapper.find("PageComponent").prop("claim")).toEqual(claim);
    });

    it("renders the wrapper component", () => {
      render();

      expect(wrapper.find("PageComponent").exists()).toBe(true);
      expect(wrapper.find("Spinner").exists()).toBe(false);
    });
  });
});
