import BenefitsApplication from "../../src/models/BenefitsApplication";
import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withBenefitsApplication from "../../src/hoc/withBenefitsApplication";

jest.mock("../../src/hooks/useAppLogic");

describe("withBenefitsApplication", () => {
  let appLogic, claim_id, wrapper;

  const PageComponent = () => <div />;
  const WrappedComponent = withBenefitsApplication(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(
        <WrappedComponent appLogic={appLogic} query={{ claim_id }} />
      );
    });
  }

  beforeEach(() => {
    claim_id = "mock-application-id";
    appLogic = useAppLogic();
  });

  it("Shows spinner when claim is not loaded", () => {
    appLogic.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings.mockReturnValue(
      false
    );

    render();

    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper.find("PageComponent").exists()).toBe(false);
  });

  it("Shows spinner when claim's warnings aren't loaded", () => {
    const claim = new BenefitsApplication({ application_id: claim_id });
    appLogic.benefitsApplications.benefitsApplications =
      new BenefitsApplicationCollection([claim]);
    appLogic.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings.mockReturnValue(
      false
    );

    render();

    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper.find("PageComponent").exists()).toBe(false);
  });

  it("loads the claim", () => {
    appLogic.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings.mockReturnValue(
      false
    );

    render();

    expect(appLogic.benefitsApplications.load).toHaveBeenCalledTimes(1);
  });

  it("does not load claim if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;
    render();
    wrapper.update();
    expect(appLogic.benefitsApplications.load).not.toHaveBeenCalled();
  });

  describe("when claim is loaded", () => {
    let claim;

    beforeEach(() => {
      claim = new BenefitsApplication({ application_id: claim_id });
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection([claim]);
      appLogic.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings.mockReturnValue(
        true
      );
    });

    it("passes through the 'user' prop from the withUser higher order component", () => {
      render();

      expect(wrapper.find("PageComponent").prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claim' prop on the passed component", () => {
      render();

      expect(wrapper.find("PageComponent").prop("claim")).toBeInstanceOf(
        BenefitsApplication
      );
      expect(wrapper.find("PageComponent").prop("claim")).toEqual(claim);
    });

    it("renders the wrapped component", () => {
      render();

      expect(wrapper.find("PageComponent").exists()).toBe(true);
      expect(wrapper.find("Spinner").exists()).toBe(false);
    });
  });
});
