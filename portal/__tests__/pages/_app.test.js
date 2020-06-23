import React, { useEffect } from "react";
import { mockRouter, mockRouterEvents } from "next/router";
import { mount, shallow } from "enzyme";
import { App } from "../../src/pages/_app";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import { NetworkError } from "../../src/errors";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import tracker from "../../src/services/tracker";
import usersApi from "../../src/api/usersApi";

jest.mock("../../src/services/tracker");
jest.mock("../../src/api/usersApi");
jest.mock("lodash/uniqueId", () => {
  return jest.fn().mockReturnValue("mocked-for-snapshots");
});

function render(customProps = {}, mountComponent = false) {
  const TestComponent = () => <div>Hello world</div>;

  const props = Object.assign(
    {
      Component: TestComponent, // allows us to do .find("TestComponent")
      pageProps: {
        title: "Test page",
      },
      initialAuthState: "signedIn",
      initialAuthData: {
        attributes: { email: "mocked-header-user@example.com" },
      },
    },
    customProps
  );

  const component = <App {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("App", () => {
  const scrollToSpy = jest.fn();
  global.scrollTo = scrollToSpy;

  beforeEach(() => {
    // Enable rendering of the site
    process.env.featureFlags = {
      pfmlTerriyay: true,
    };
  });

  describe("when the 'pfmlTerriyay' feature flag is disabled", () => {
    it("doesn't render the site", () => {
      process.env.featureFlags = {
        pfmlTerriyay: false,
      };

      const { wrapper } = render();

      expect(wrapper).toMatchInlineSnapshot(`
        <code>
          Hello world (◕‿◕)
        </code>
      `);
    });
  });

  describe("when a user IS authenticated", () => {
    let wrapper;

    beforeEach(async () => {
      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const props = {
        initialAuthState: "signedIn",
        initialAuthData: {
          attributes: { email: "mocked-header-user@example.com" },
        },
      };

      // Authenticator causes async state updates
      await act(async () => {
        wrapper = render(props, mountComponent).wrapper;
      });

      // Re-render after async effects
      wrapper.update();
    });

    it("fetches the user from the API", () => {
      expect(usersApi.getCurrentUser).toHaveBeenCalledTimes(1);
    });

    it("renders the site header with the authenticated user's info", () => {
      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toMatchInlineSnapshot(`
        Object {
          "username": "mocked-header-user@example.com",
        }
      `);
    });
  });

  describe("when authenticated user consented to data sharing", () => {
    let wrapper;

    beforeEach(async () => {
      usersApi.getCurrentUser.mockResolvedValueOnce({
        success: true,
        user: new User({
          auth_id: "mock-auth-id",
          consented_to_data_sharing: true,
          user_id: "mock-user-id",
          email_address: "mock@example.com",
        }),
      });

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      // Authenticator causes async state updates
      await act(async () => {
        wrapper = render({}, mountComponent).wrapper;
      });

      // Re-render after async effects
      wrapper.update();
    });

    it("renders the page component", () => {
      const component = wrapper.find("TestComponent");

      expect(component).toMatchSnapshot();
    });

    it("doesn't redirect to the consent page", () => {
      expect(mockRouter.push).not.toHaveBeenCalled();
    });
  });

  describe("when authenticated user hasn't consented to data sharing", () => {
    let wrapper;

    beforeEach(async () => {
      usersApi.getCurrentUser.mockResolvedValueOnce({
        success: true,
        user: new User({
          auth_id: "mock-auth-id",
          consented_to_data_sharing: false,
          user_id: "mock-user-id",
          email_address: "mock@example.com",
        }),
      });

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      // Authenticator causes async state updates
      await act(async () => {
        wrapper = render({}, mountComponent).wrapper;
      });

      // Re-render after async effects
      wrapper.update();
    });

    it("redirects to the consent page", () => {
      expect(mockRouter.push).toHaveBeenCalledWith(
        "/user/consent-to-data-sharing"
      );
    });
  });

  describe("when the authenticated user fails to be fetched from the API", () => {
    const initialAuthProps = {
      initialAuthState: "signedIn",
      initialAuthData: {
        attributes: { email: "mocked-header-user@example.com" },
      },
    };

    beforeEach(() => {
      // We expect console.error to be called in this scenario
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    });

    it("displays error for NetworkError", async () => {
      expect.assertions();
      usersApi.getCurrentUser.mockRejectedValueOnce(new NetworkError());

      let wrapper;
      await act(async () => {
        wrapper = render(initialAuthProps, true).wrapper;
      });
      wrapper.update();

      expect(wrapper.find("ErrorsSummary").prop("errors")).toMatchSnapshot();
    });

    it("displays error for unsuccessful response", async () => {
      expect.assertions();
      usersApi.getCurrentUser.mockResolvedValueOnce({ success: false });

      let wrapper;
      await act(async () => {
        wrapper = render(initialAuthProps, true).wrapper;
      });
      wrapper.update();

      expect(wrapper.find("ErrorsSummary").prop("errors")).toMatchSnapshot();
    });
  });

  describe("when a user is NOT authenticated", () => {
    const initialAuthState = "signIn";
    const initialAuthData = undefined;
    const authProps = { initialAuthState, initialAuthData };

    it("does not attempt to fetch a user from the API", () => {
      render(authProps);

      expect(usersApi.getCurrentUser).toHaveBeenCalledTimes(0);
    });

    it("renders the site header without a user", () => {
      const { wrapper } = render(authProps);

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toBeUndefined();
    });
  });

  describe("when the Authenticator authState changes to something other than 'signedIn'", () => {
    it("updates the authState prop on Authenticator", () => {
      const { wrapper } = render();
      const authState = "customAuthState";
      const authData = {};

      act(() => {
        wrapper
          .find("Authenticator")
          .simulate("stateChange", authState, authData);
      });

      expect(wrapper.find("Authenticator").prop("authState")).toBe(authState);
    });

    it("clears the authUser state", () => {
      const { wrapper } = render();
      const authState = "signIn";
      const authData = {};

      act(() => {
        wrapper
          .find("Authenticator")
          .simulate("stateChange", authState, authData);
      });

      // There isn't a clear way in Enzyme to read the state from useState (yet)
      // so we assert on the authData value that gets passed into Header
      expect(wrapper.find("Header").prop("user")).toBeUndefined();
    });
  });

  describe("when the Authenticator authState changes to 'signedIn'", () => {
    const initialAuthState = "signIn";
    const initialAuthData = undefined;
    const initialAuthProps = { initialAuthState, initialAuthData };
    const authState = "signedIn";
    const authData = { attributes: { email: "foo@example.com " } };

    it("fetches user from the API", async () => {
      expect.assertions();

      const { wrapper } = render(initialAuthProps);

      await act(async () => {
        wrapper
          .find("Authenticator")
          .simulate("stateChange", authState, authData);
      });

      expect(usersApi.getCurrentUser).toHaveBeenCalledTimes(1);
    });
  });

  describe("Router events", () => {
    it("displays the spinner when a route change starts", async () => {
      expect.assertions(2);

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      const routeChangeStart = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeStart"
      );
      await act(async () => {
        // Wait for repaint
        await new Promise((resolve) => setTimeout(resolve, 0));
        // Trigger routeChangeStart
        routeChangeStart.callback();
      });

      wrapper.update();

      expect(wrapper.find("Spinner").exists()).toBe(true);
      expect(wrapper.find("TestComponent").exists()).toBe(false);
    });

    it("hides spinner and sets New Relic route name when a route change completes", async () => {
      expect.assertions();

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);
      const newUrl = "/claims?claim_id=123";

      const routeChangeStart = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeStart"
      );
      const routeChangeComplete = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeComplete"
      );

      await act(async () => {
        // Wait for repaint
        await new Promise((resolve) => setTimeout(resolve, 0));

        // Trigger routeChangeStart
        routeChangeStart.callback(newUrl);
        // Trigger routeChangeComplete
        routeChangeComplete.callback(newUrl);

        wrapper.update();
      });

      expect(wrapper.find("Spinner").exists()).toBe(false);
      expect(wrapper.find("TestComponent").exists()).toBe(true);
      expect(tracker.setCurrentRouteName).toHaveBeenCalledTimes(1);
      expect(tracker.setCurrentRouteName).toHaveBeenCalledWith("/claims");
    });

    it("hides spinner when a route change throws an error", async () => {
      expect.assertions(2);

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      const routeChangeStart = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeStart"
      );
      const routeChangeError = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeError"
      );
      await act(async () => {
        // Wait for repaint
        await new Promise((resolve) => setTimeout(resolve, 0));

        // Trigger routeChangeStart
        routeChangeStart.callback();
        // Trigger routeChangeError
        routeChangeError.callback();

        wrapper.update();
      });

      // Spinner hidden when route change ended
      expect(wrapper.find("Spinner").exists()).toBe(false);
      expect(wrapper.find("TestComponent").exists()).toBe(true);
    });

    it("scrolls to the top of the window after a route change", async () => {
      expect.assertions(1);

      // Mount the component so that useEffect is called.
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      const routeChangeStart = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeStart"
      );
      const routeChangeComplete = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeComplete"
      );

      await act(async () => {
        // Wait for repaint
        await new Promise((resolve) => setTimeout(resolve, 0));

        // Trigger routeChangeStart
        routeChangeStart.callback();
        // Trigger routeChangeComplete
        routeChangeComplete.callback();

        wrapper.update();
      });

      expect(scrollToSpy).toHaveBeenCalled();
    });
  });

  describe("displaying errors", () => {
    it("displays errors that child pages set", async () => {
      const ChildPage = (props) => {
        const { setAppErrors } = props; // eslint-disable-line react/prop-types
        useEffect(() => {
          const message = "A test error happened";
          setAppErrors([new AppErrorInfo({ message })]);
        }, [setAppErrors]);
        return <React.Fragment />;
      };

      let wrapper;

      // Authenticator causes async state updates
      await act(async () => {
        wrapper = render({ Component: ChildPage }, true).wrapper;
      });
      wrapper.update();

      expect(wrapper.find("ErrorsSummary").prop("errors")).toMatchSnapshot();
    });
  });
});
