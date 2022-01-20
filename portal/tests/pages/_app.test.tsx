// @ts-expect-error Not sure how else to track occurrences of these
import { mockRouter, mockRouterEvents } from "next/router";
import { render, screen } from "@testing-library/react";
import { App } from "../../src/pages/_app";
import { MockRouterEvent } from "../../lib/mock-helpers/router";
import React from "react";
import { act } from "react-dom/test-utils";
import useTrackerPageView from "../../src/hooks/useTrackerPageView";

// see https://github.com/vercel/next.js/issues/5416
jest.mock("next/dynamic", () => () => () => null);
jest.mock("../../src/api/UsersApi");
jest.mock("../../src/hooks/useAppLogic");
jest.mock("../../src/hooks/useTrackerPageView");
jest.mock("lodash/uniqueId", () => {
  return jest.fn().mockReturnValue("mocked-for-snapshots");
});

function renderApp() {
  const TestComponent = () => (
    <div>
      <h1 tabIndex={-1} className="js-title">
        Page title
      </h1>
    </div>
  );

  const component = (
    <App Component={TestComponent} pageProps={{}} router={mockRouter} />
  );
  return render(component);
}

describe("App", () => {
  const scrollToSpy = jest.fn();
  global.scrollTo = scrollToSpy;

  beforeEach(() => {
    // Enable rendering of the site
    process.env.featureFlags = JSON.stringify({
      pfmlTerriyay: true,
    });

    // Reset the focused element
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
  });

  describe("Router events", () => {
    const triggerRouterEvent = async (
      eventName: string,
      url = "/foo",
      options: {
        shallow?: boolean;
      } = {}
    ) => {
      const routeChangeStart = mockRouterEvents.find(
        (evt: MockRouterEvent) => evt.name === eventName
      );

      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
        routeChangeStart.callback(url, options);
      });
    };

    it("sets isLoading to true when a route change starts", async () => {
      renderApp();
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();

      await triggerRouterEvent("routeChangeStart");

      expect(screen.queryByRole("progressbar")).toBeInTheDocument();
    });

    it("does not set isLoading to true when a SHALLOW route change starts", async () => {
      renderApp();

      await triggerRouterEvent("routeChangeStart", undefined, {
        shallow: true,
      });
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });

    it("does not scroll to the top of the window after a SHALLOW route change", async () => {
      renderApp();

      await triggerRouterEvent("routeChangeStart", undefined, {
        shallow: true,
      });
      await triggerRouterEvent("routeChangeComplete", undefined, {
        shallow: true,
      });

      expect(scrollToSpy).not.toHaveBeenCalled();
    });

    it("calls useTrackerPageView hook when mounted", () => {
      renderApp();
      expect(useTrackerPageView).toHaveBeenCalledTimes(1);
    });

    it("moves focus to .js-title after a route change completes", async () => {
      renderApp();

      await triggerRouterEvent("routeChangeComplete");

      const h1 = screen.getByRole("heading");

      expect(h1).toHaveFocus();
    });

    it("does not move focus to .js-title after a route change completes", async () => {
      renderApp();

      await triggerRouterEvent("routeChangeComplete", undefined, {
        shallow: true,
      });

      const h1 = screen.getByRole("heading");

      expect(h1).not.toHaveFocus();
    });
  });
});
