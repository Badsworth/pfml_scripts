/* eslint-disable import/first */
jest.mock("aws-amplify");

// We need to manually trigger Router events to test their side effects
let mockRouterEvents = [];
jest.mock("next/router", () => ({
  events: {
    on: (name, callback) => {
      mockRouterEvents.push({ name, callback });
    },
    off: jest.fn(),
  },
}));

import { mount, shallow } from "enzyme";
import { App } from "../../src/pages/_app";
import { Auth } from "aws-amplify";
import React from "react";
import { act } from "react-dom/test-utils";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      Component: () => <div />,
      pageProps: {},
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
  afterEach(() => {
    mockRouterEvents = [];
  });

  describe("when a user is authenticated", () => {
    it("renders the site header with the authenticated user's info", async () => {
      Auth.currentAuthenticatedUser.mockResolvedValueOnce({
        attributes: {
          email: "mocked-header-user@example.com",
        },
      });

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      // We need to wait a hot second for async authentication and state update
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        wrapper.update();
      });

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toMatchInlineSnapshot(`
      Object {
        "username": "mocked-header-user@example.com",
      }
    `);
    });
  });

  describe("when currentAuthenticatedUser throws an error", () => {
    beforeAll(() => {
      // Don't show a scary error in our log when it's expected
      jest.spyOn(console, "error").mockImplementation(() => null);
    });

    afterAll(() => {
      console.error.mockRestore();
    });

    it("renders the site header without a user", async () => {
      Auth.currentAuthenticatedUser.mockRejectedValueOnce(
        Error("Mocked rejection")
      );

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      // We need to wait a hot second for async authentication and state update
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        wrapper.update();
      });

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toEqual({});
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
        title="Test page"
      />
    `);
  });

  describe("Router events", () => {
    beforeEach(() => {
      Auth.currentAuthenticatedUser.mockResolvedValueOnce({
        attributes: {
          email: "mocked-header-user@example.com",
        },
      });
    });

    it("displays the spinner when a route change starts", async () => {
      expect.assertions(2);

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      const routeChangeStart = mockRouterEvents.find(
        evt => evt.name === "routeChangeStart"
      );
      await act(async () => {
        // Wait for repaint
        await new Promise(resolve => setTimeout(resolve, 0));
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
        evt => evt.name === "routeChangeStart"
      );
      const routeChangeComplete = mockRouterEvents.find(
        evt => evt.name === "routeChangeComplete"
      );

      await act(async () => {
        // Wait for repaint
        await new Promise(resolve => setTimeout(resolve, 0));

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
        evt => evt.name === "routeChangeStart"
      );
      const routeChangeError = mockRouterEvents.find(
        evt => evt.name === "routeChangeError"
      );
      await act(async () => {
        // Wait for repaint
        await new Promise(resolve => setTimeout(resolve, 0));

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
