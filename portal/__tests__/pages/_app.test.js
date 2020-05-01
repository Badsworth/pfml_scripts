import { mount, shallow } from "enzyme";
import { App } from "../../src/pages/_app";
import React from "react";
import { act } from "react-dom/test-utils";
import { mockRouterEvents } from "next/router";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      Component: () => <div />,
      pageProps: {},
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

  describe("when a user IS authenticated", () => {
    it("renders the site header with the authenticated user's info", () => {
      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toMatchInlineSnapshot(`
        Object {
          "username": "mocked-header-user@example.com",
        }
      `);
    });
  });

  describe("when a user is NOT authenticated", () => {
    const initialAuthState = "signIn";
    const initialAuthData = undefined;
    const authProps = { initialAuthState, initialAuthData };

    it("renders the site header without a user", () => {
      const { wrapper } = render(authProps);

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toBeUndefined();
    });
  });

  describe("when the Authenticator authState changes", () => {
    it("sets the authUser state when the new authState is 'signedIn'", () => {
      const { wrapper } = render();
      const authState = "signedIn";
      const authData = { attributes: { email: "foo@example.com " } };

      wrapper
        .find("Authenticator")
        .simulate("stateChange", authState, authData);

      // There isn't a clear way in Enzyme to read the state from useState (yet)
      // so we assert on the authData value that gets passed into Header
      expect(wrapper.find("Header").prop("user")).toMatchInlineSnapshot(`
        Object {
          "username": "foo@example.com ",
        }
      `);
    });

    it("clears the authUser state when the new authState is NOT 'signedIn'", () => {
      const { wrapper } = render();
      const authState = "signIn";
      const authData = {};

      wrapper
        .find("Authenticator")
        .simulate("stateChange", authState, authData);

      // There isn't a clear way in Enzyme to read the state from useState (yet)
      // so we assert on the authData value that gets passed into Header
      expect(wrapper.find("Header").prop("user")).toBeUndefined();
    });

    it("updates the authState prop on Authenticator", () => {
      const { wrapper } = render();
      const authState = "customAuthState";
      const authData = {};

      wrapper
        .find("Authenticator")
        .simulate("stateChange", authState, authData);

      expect(wrapper.find("Authenticator").prop("authState")).toBe(authState);
    });
  });

  it("renders the passed in Component with the given pageProps", () => {
    const TestComponent = () => <div>Hello world</div>;

    const { wrapper } = render({
      Component: TestComponent,
      pageProps: {
        title: "Test page",
      },
    });

    const component = wrapper.find("TestComponent");

    expect(component).toMatchInlineSnapshot(`
      <TestComponent
        claims={
          Collection {
            "byId": Object {},
            "idProperty": "claim_id",
            "ids": Array [],
          }
        }
        query={Object {}}
        setUser={[Function]}
        title="Test page"
        user={
          User {
            "cognito_user_id": null,
            "date_of_birth": null,
            "first_name": null,
            "has_state_id": null,
            "last_name": null,
            "middle_name": null,
            "ssn_or_itin": null,
            "state_id": null,
            "status": null,
            "user_id": null,
          }
        }
      />
    `);
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
        wrapper.update();
      });

      expect(wrapper.find("Spinner").exists()).toBe(true);
      expect(wrapper.find("Component").exists()).toBe(false);
    });

    it("hides spinner when a route change completes", async () => {
      expect.assertions(2);

      // We need to mount the component so that useEffect is called
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

      expect(wrapper.find("Spinner").exists()).toBe(false);
      expect(wrapper.find("Component").exists()).toBe(true);
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
      expect(wrapper.find("Component").exists()).toBe(true);
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
});
