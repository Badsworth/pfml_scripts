import React, { useEffect } from "react";
import { mount, shallow } from "enzyme";
import { App } from "../../src/pages/_app";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { act } from "react-dom/test-utils";
import { mockRouterEvents } from "next/router";
import tracker from "../../src/services/tracker";

// see https://github.com/vercel/next.js/issues/5416
jest.mock("next/dynamic", () => () => (props) => null);
jest.mock("../../src/services/tracker");
jest.mock("../../src/api/UsersApi");
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
      expect(tracker.startPageView).toHaveBeenCalledTimes(1);
      expect(tracker.startPageView).toHaveBeenCalledWith("/claims");
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

  describe("displaying errors", () => {
    it("displays errors that child pages set", () => {
      const ChildPage = (props) => {
        const {
          appLogic: { setAppErrors }, // eslint-disable-line react/prop-types
        } = props;
        useEffect(() => {
          const message = "A test error happened";
          setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo({ message })])
          );
        }, [setAppErrors]);
        return <React.Fragment />;
      };

      let wrapper;

      act(() => {
        wrapper = render({ Component: ChildPage }, true).wrapper;
      });
      wrapper.update();

      expect(wrapper.find("ErrorsSummary").prop("errors")).toMatchSnapshot();
    });
  });
});
