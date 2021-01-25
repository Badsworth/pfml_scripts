import { mount, shallow } from "enzyme";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import React from "react";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import useAppLogic from "../../src/hooks/useAppLogic";
import withUser from "../../src/hoc/withUser";

jest.mock("../../src/hooks/useAppLogic");

describe("withUser", () => {
  let appLogic, wrapper;

  const PageComponent = (props) => <div />;
  const WrappedComponent = withUser(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(<WrappedComponent appLogic={appLogic} />);
    });
  }

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  it("Shows spinner when user is not loaded", () => {
    appLogic.users.user = null;
    act(() => {
      wrapper = shallow(<WrappedComponent appLogic={appLogic} />);
    });
    expect(wrapper).toMatchInlineSnapshot(`
      <div
        className="margin-top-8 text-center"
      >
        <Spinner
          aria-valuetext="Loading account"
        />
      </div>
    `);
  });

  it("loads the user if logged in", () => {
    appLogic.auth.isLoggedIn = true;
    appLogic.users.user = null;
    render();
    expect(appLogic.users.loadUser).toHaveBeenCalled();
  });

  it("does not load user if logged out", () => {
    appLogic.auth.isLoggedIn = false;
    appLogic.users.user = null;
    render();
    expect(appLogic.users.loadUser).not.toHaveBeenCalled();
  });

  it("does not load user if logged in status has not been checked yet", () => {
    appLogic.auth.isLoggedIn = null;
    appLogic.users.user = null;
    render();
    expect(appLogic.users.loadUser).not.toHaveBeenCalled();
  });

  it("does not load user if there is an error", () => {
    appLogic.appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);
    render();
    expect(appLogic.users.loadUser).not.toHaveBeenCalled();
  });

  it("calls requireLogin in all situations", () => {
    appLogic.users.user = new User();
    render();
    expect(appLogic.auth.requireLogin).toHaveBeenCalled();

    appLogic.auth.isLoggedIn = true;
    appLogic.users.user = null;
    render();
    expect(appLogic.auth.requireLogin).toHaveBeenCalled();

    appLogic.auth.isLoggedIn = false;
    appLogic.users.user = null;
    render();
    expect(appLogic.auth.requireLogin).toHaveBeenCalled();
  });

  describe("when authenticated user consented to data sharing", () => {
    beforeEach(() => {
      appLogic.users.user = new User({ consented_to_data_sharing: true });
      render();
    });

    it("sets the 'user' prop on the passed component to the logged in user object", () => {
      const pageComponent = wrapper.find("PageComponent");
      expect(pageComponent.prop("user")).toBe(appLogic.users.user);
    });

    it("renders the page component", () => {
      expect(wrapper.childAt(0).name()).toBe("PageComponent");
    });

    it("doesn't redirect to the consent page", () => {
      expect(mockRouter.push).not.toHaveBeenCalled();
    });
  });

  describe("when authenticated user hasn't consented to data sharing", () => {
    beforeEach(() => {
      appLogic.users.user = new User({ consented_to_data_sharing: false });
      render();
    });

    it("does not render the wrapped component", () => {
      expect(wrapper.isEmptyRender()).toBeTruthy();
    });

    it("calls requireUserConsentToDataAgreement", () => {
      expect(
        appLogic.users.requireUserConsentToDataAgreement
      ).toHaveBeenCalled();
    });
  });
});
