import { mount, shallow } from "enzyme";
import { App } from "../../src/pages/_app";
import React from "react";
import { act } from "react-dom/test-utils";
import { mockRouterEvents } from "next/router";
import tracker from "../../src/services/tracker";

// see https://github.com/vercel/next.js/issues/5416
jest.mock("next/dynamic", () => () => (_props) => null);
jest.mock("../../src/services/tracker");
jest.mock("../../src/api/UsersApi");
jest.mock("lodash/uniqueId", () => {
  return jest.fn().mockReturnValue("mocked-for-snapshots");
});

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      Component: () => <div>Hello world</div>,
    },
    customProps
  );

  const component = <App {...props} />;
  const container = document.createElement("div");
  container.id = "enzymeContainer";
  document.body.appendChild(container);

  return {
    props,
    wrapper: mountComponent
      ? mount(component, {
          // attachTo the body so document.activeElement works (https://github.com/enzymejs/enzyme/issues/2337#issuecomment-608984530)
          attachTo: container,
        })
      : shallow(component),
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

  describe("Router events", () => {
    it("sets isLoading to true when a route change starts", async () => {
      expect.assertions();

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

      expect(wrapper.find("PageWrapper").prop("isLoading")).toBe(true);
    });

    it("sets isLoading to false and sets New Relic route name when a route change completes", async () => {
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

      expect(wrapper.find("PageWrapper").prop("isLoading")).toBe(false);
      expect(tracker.startPageView).toHaveBeenCalledTimes(1);
      expect(tracker.startPageView).toHaveBeenCalledWith(
        "/claims",
        expect.objectContaining({ query_claim_id: "123" })
      );
    });

    it("sets isLoading to false when a route change throws an error", async () => {
      expect.assertions();

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

      expect(wrapper.find("PageWrapper").prop("isLoading")).toBe(false);
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

    it("moves focus to .js-title after a route change completes", () => {
      expect.assertions(1);

      // Mount the component so that useEffect is called.
      const mountComponent = true;
      // Create page content that includes the h1 with expected markup
      const TestComponent = () => (
        <div>
          <h1 tabIndex="-1" className="js-title">
            Page title
          </h1>
        </div>
      );
      const { wrapper } = render(
        {
          Component: TestComponent,
        },
        mountComponent
      );

      const routeChangeComplete = mockRouterEvents.find(
        (evt) => evt.name === "routeChangeComplete"
      );

      act(() => {
        // Trigger routeChangeComplete
        routeChangeComplete.callback();
      });

      const h1 = wrapper.find("h1").last().getDOMNode();

      expect(document.activeElement).toBe(h1);
    });
  });
});
