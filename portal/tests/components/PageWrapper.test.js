import PageWrapper from "../../src/components/PageWrapper";
import React from "react";
import { mockRouter } from "next/router";
import { shallow } from "enzyme";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

// see https://github.com/vercel/next.js/issues/5416
jest.mock("next/dynamic", () => () => (_props) => null);

function render(customProps = {}) {
  let appLogic;

  testHook(() => {
    appLogic = useAppLogic();
  });

  return shallow(
    <PageWrapper
      appLogic={appLogic}
      children={<div>Page</div>}
      {...customProps}
    />
  );
}

describe("PageWrapper", () => {
  beforeEach(() => {
    // Enable rendering of the site
    process.env.featureFlags = {
      pfmlTerriyay: true,
    };
  });

  it("doesn't render the site when the 'pfmlTerriyay' feature flag is disabled", () => {
    process.env.featureFlags = {
      pfmlTerriyay: false,
    };

    const wrapper = render();

    expect(wrapper).toMatchInlineSnapshot(`
        <code>
          Hello world (◕‿◕)
        </code>
      `);
  });

  it("sets description meta tag", () => {
    const wrapper = render();

    expect(wrapper.find("meta")).toMatchSnapshot();
  });

  it("renders the Header", () => {
    let appLogic;
    testHook(() => {
      appLogic = useAppLogic();
    });

    const wrapper = render({ appLogic });

    expect(wrapper.find("Header").exists()).toBe(true);
    expect(wrapper.find("Header").prop("user")).toBe(appLogic.users.user);
    expect(wrapper.find("Header").prop("onLogout")).toBe(appLogic.auth.logout);
  });

  it("renders Spinner when isLoading is true", () => {
    const wrapper = render({ isLoading: true });

    expect(wrapper.find("#page")).toMatchSnapshot();
  });

  it("renders the children as the page's body", () => {
    const wrapper = render({ children: <p>Page content</p> });

    expect(wrapper.find("#page")).toMatchInlineSnapshot(`
      <section
        id="page"
      >
        <p>
          Page content
        </p>
      </section>
    `);
  });

  it("renders MaintenanceTakeover when maintenancePageRoutes includes the current page's route", () => {
    mockRouter.pathname = "/login";

    const wrapper = render({ maintenancePageRoutes: ["/login"] });

    // Need to use data-test attribute since the MaintenanceTakeover component
    // is lazy-loaded, so won't be present on initial render
    expect(wrapper.find({ "data-test": "maintenance page" }).exists()).toBe(
      true
    );
  });

  it("renders MaintenanceTakeover when maintenancePageRoutes includes a wildcard matching the current page's route", () => {
    let wrapper;
    const maintenancePageRoutes = ["/employers/*"];

    // Doesn't render for a page that doesn't match the wildcard
    mockRouter.pathname = "/foo";
    wrapper = render({ maintenancePageRoutes });
    expect(wrapper.find({ "data-test": "maintenance page" }).exists()).toBe(
      false
    );

    // Matches base pathname
    mockRouter.pathname = "/employers/";
    wrapper = render({ maintenancePageRoutes });
    expect(wrapper.find({ "data-test": "maintenance page" }).exists()).toBe(
      true
    );

    // Matches sub-pages
    mockRouter.pathname = "/employers/create-account";
    wrapper = render({ maintenancePageRoutes });
    expect(wrapper.find({ "data-test": "maintenance page" }).exists()).toBe(
      true
    );
  });

  it("bypasses MaintenanceTakeover when noMaintenance feature flag is present", () => {
    process.env.featureFlags = {
      noMaintenance: true,
      pfmlTerriyay: true,
    };
    mockRouter.pathname = "/login";

    const wrapper = render({ maintenancePageRoutes: ["/login"] });

    expect(wrapper.find({ "data-test": "maintenance page" }).exists()).toBe(
      false
    );
  });

  it("sets errors prop on ErrorsSummary", () => {
    let appLogic;
    testHook(() => {
      appLogic = useAppLogic();
    });

    const wrapper = render({ appLogic });

    expect(wrapper.find("ErrorsSummary").prop("errors")).toBe(
      appLogic.appErrors
    );
  });
});
