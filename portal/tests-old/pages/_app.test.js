import { App } from "../../src/pages/_app";
import React from "react";
import { act } from "react-dom/test-utils";
import { merge } from "lodash";
import { mockRouterEvents } from "next/router";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import useTrackerPageView from "../../src/hooks/useTrackerPageView";

// see https://github.com/vercel/next.js/issues/5416
jest.mock("next/dynamic", () => () => (_props) => null);
jest.mock("../../src/api/UsersApi");
jest.mock("../../src/hooks/useAppLogic");
jest.mock("../../src/hooks/useTrackerPageView.js");
jest.mock("lodash/uniqueId", () => {
  return jest.fn().mockReturnValue("mocked-for-snapshots");
});

function render() {
  const TestComponent = () => (
    <div>
      <h1 tabIndex="-1" className="js-title">
        Page title
      </h1>
    </div>
  );

  const component = <App Component={TestComponent} />;
  const container = document.createElement("div");
  container.id = "enzymeContainer";
  document.body.appendChild(container);

  return {
    // Mount so useEffect is triggered
    wrapper: mount(component, {
      // attachTo the body so document.activeElement works (https://github.com/enzymejs/enzyme/issues/2337#issuecomment-608984530)
      attachTo: container,
    }),
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

    // Reset the focused element
    document.activeElement.blur();
  });

  describe("Router events", () => {
    const triggerRouterEvent = async (
      eventName,
      url = "/foo",
      options = {}
    ) => {
      const routeChangeStart = mockRouterEvents.find(
        (evt) => evt.name === eventName
      );

      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
        routeChangeStart.callback(url, options);
      });
    };

    it("sets isLoading to true when a route change starts", async () => {
      expect.assertions();

      const { wrapper } = render();
      await triggerRouterEvent("routeChangeStart");
      wrapper.update();

      expect(wrapper.find("PageWrapper").prop("isLoading")).toBe(true);
    });

    it("does not set isLoading to true when a SHALLOW route change starts", async () => {
      expect.assertions();
      const { wrapper } = render();

      await triggerRouterEvent("routeChangeStart", undefined, {
        shallow: true,
      });
      wrapper.update();

      expect(wrapper.find("PageWrapper").prop("isLoading")).toBe(false);
    });

    it("does not scroll to the top of the window after a SHALLOW route change", async () => {
      expect.assertions(1);
      render();

      await triggerRouterEvent("routeChangeStart", undefined, {
        shallow: true,
      });
      await triggerRouterEvent("routeChangeComplete", undefined, {
        shallow: true,
      });

      expect(scrollToSpy).not.toHaveBeenCalled();
    });

    it("calls useTrackerPageView hook when mounted", () => {
      // Overwrite isLoggedIn to simulate a scenario where the route event is
      // triggered before the page has loaded auth info
      useAppLogic.mockImplementationOnce(() =>
        merge(
          { ...useAppLogic() },
          {
            auth: { isLoggedIn: null },
          }
        )
      );

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      render(mountComponent);
      expect(useTrackerPageView).toHaveBeenCalledTimes(1);
    });

    it("moves focus to .js-title after a route change completes", async () => {
      expect.assertions(1);
      const { wrapper } = render();

      await triggerRouterEvent("routeChangeComplete");

      const h1 = wrapper.find("h1").last().getDOMNode();

      expect(document.activeElement).toEqual(h1);
    });

    it("does not move focus to .js-title after a route change completes", async () => {
      expect.assertions(1);
      const { wrapper } = render();

      await triggerRouterEvent("routeChangeComplete", undefined, {
        shallow: true,
      });

      const h1 = wrapper.find("h1").last().getDOMNode();

      expect(document.activeElement).not.toEqual(h1);
    });
  });
});
