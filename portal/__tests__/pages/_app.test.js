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
      authState: "signedIn",
      authData: { attributes: { email: "mocked-header-user@example.com" } },
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
    const authState = "signIn";
    const authData = undefined;
    const authProps = { authState, authData };

    it("renders the site header without a user", () => {
      const { wrapper } = render(authProps);

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toBeUndefined();
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
            "idProperty": "claimId",
            "ids": Array [],
          }
        }
        query={Object {}}
        setUser={[Function]}
        title="Test page"
        user={
          User {
            "cognitoUserId": null,
            "dateOfBirth": null,
            "firstName": null,
            "hasStateId": null,
            "lastName": null,
            "middleName": null,
            "ssn": null,
            "stateId": null,
            "status": null,
            "userId": null,
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
  });
});
