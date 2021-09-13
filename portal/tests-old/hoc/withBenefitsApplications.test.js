import { mount, shallow } from "enzyme";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";
import withBenefitsApplications from "../../src/hoc/withBenefitsApplications";

jest.mock("../../src/hooks/useAppLogic");

describe("withBenefitsApplications", () => {
  let appLogic, wrapper;

  const PageComponent = (props) => <div />;
  const WrappedComponent = withBenefitsApplications(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(<WrappedComponent appLogic={appLogic} />);
    });
  }

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  it("Shows spinner when claims are not loaded", () => {
    appLogic.benefitsApplications.benefitsApplications =
      new BenefitsApplicationCollection();
    act(() => {
      wrapper = shallow(<WrappedComponent appLogic={appLogic} />);
    });
    expect(wrapper.dive()).toMatchInlineSnapshot(`
      <div
        className="margin-top-8 text-center"
      >
        <Spinner
          aria-valuetext="Loading applications"
        />
      </div>
    `);
  });

  it("loads claims", () => {
    appLogic.benefitsApplications.benefitsApplications =
      new BenefitsApplicationCollection();
    render();
    expect(appLogic.benefitsApplications.loadAll).toHaveBeenCalledTimes(1);
  });

  it("does not load claims if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;
    render();
    wrapper.update();
    expect(appLogic.benefitsApplications.loadAll).not.toHaveBeenCalled();
  });

  it("does not load claims if claims have already been loaded", () => {
    appLogic.benefitsApplications.benefitsApplications =
      new BenefitsApplicationCollection([]);
    appLogic.benefitsApplications.hasLoadedAll = true;

    render();
    expect(appLogic.benefitsApplications.loadAll).not.toHaveBeenCalled();
  });

  describe("when claims are loaded", () => {
    beforeEach(() => {
      // Mock initial state of the app
      // these values would be passed from _app.js
      const claim = new BenefitsApplication({
        application_id: "mock-application-id",
      });
      const claims = new BenefitsApplicationCollection([claim]);
      appLogic.benefitsApplications.benefitsApplications = claims;
      appLogic.benefitsApplications.hasLoadedAll = true;
      render();
    });

    it("passes through the 'user' prop from the withUser higher order component", () => {
      expect(wrapper.find(PageComponent).prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claims' prop on the passed component to the loaded claims", () => {
      // Since withBenefitsApplications is wrapped by withUser, to get the wrapped page component we need to get the child twice
      expect(wrapper.find(PageComponent).prop("claims")).toBeInstanceOf(
        BenefitsApplicationCollection
      );
      expect(wrapper.find(PageComponent).prop("claims")).toEqual(
        appLogic.benefitsApplications.benefitsApplications
      );
    });

    it("renders the wrapped component", () => {
      // Since withBenefitsApplications is wrapped by withUser, to get the wrapped page component we need to get the child twice
      expect(wrapper.find(PageComponent).name()).toBe("PageComponent");
    });
  });
});
