import { DateTime } from "luxon";
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
      // eslint-disable-next-line react/no-children-prop
      children={<div>Page</div>}
      {...customProps}
    ></PageWrapper>
  );
}

function hasMaintenancePage(wrapper) {
  // Need to use data-test attribute since the MaintenanceTakeover component
  // is lazy-loaded, so won't be present on initial render
  return wrapper.find({ "data-test": "maintenance page" }).exists();
}

describe("PageWrapper", () => {
  const maintenance = {
    name: null,
    start: null,
    end: null,
    enabled: false,
    options: {
      page_routes: [],
    },
  };

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

    const wrapper = render({ maintenance });

    expect(wrapper).toMatchInlineSnapshot(`
        <code>
          Hello world (◕‿◕)
        </code>
      `);
  });

  it("sets description meta tag", () => {
    const wrapper = render({ maintenance });

    expect(wrapper.find("meta")).toMatchSnapshot();
  });

  it("renders the Header", () => {
    let appLogic;
    testHook(() => {
      appLogic = useAppLogic();
    });

    const wrapper = render({ appLogic, maintenance });

    expect(wrapper.find("Header").exists()).toBe(true);
    expect(wrapper.find("Header").prop("user")).toBe(appLogic.users.user);
    expect(wrapper.find("Header").prop("onLogout")).toBe(appLogic.auth.logout);
  });

  it("renders Spinner when isLoading is true", () => {
    const wrapper = render({ isLoading: true, maintenance });

    expect(wrapper.find("#page")).toMatchSnapshot();
  });

  it("renders the children as the page's body", () => {
    const wrapper = render({ children: <p>Page content</p>, maintenance });

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

  it("renders MaintenanceTakeover when maintenancePageRoutes includes the current page's route and no start/end time is set", () => {
    mockRouter.pathname = "/login";

    const wrapper = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/login"],
        },
      },
    });

    expect(hasMaintenancePage(wrapper)).toBe(true);
  });

  it("renders MaintenanceTakeover when maintenancePageRoutes includes a wildcard matching the current page's route", () => {
    let wrapper;

    // Doesn't render for a page that doesn't match the wildcard
    mockRouter.pathname = "/foo";
    wrapper = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/employers/*"],
        },
      },
    });
    expect(hasMaintenancePage(wrapper)).toBe(false);

    // Matches base pathname
    mockRouter.pathname = "/employers/";
    wrapper = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/employers/*"],
        },
      },
    });
    expect(hasMaintenancePage(wrapper)).toBe(true);

    // Matches sub-pages
    mockRouter.pathname = "/employers/create-account";
    wrapper = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/employers/*"],
        },
      },
    });
    expect(hasMaintenancePage(wrapper)).toBe(true);
  });

  it("renders MaintenanceTakeover with localized end time when maintenanceEnd is set", () => {
    mockRouter.pathname = "/";
    // Ends in an hour
    const maintenanceEndDateTime = DateTime.local().plus({ hours: 1 });

    const wrapperWithoutEndTime = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
      },
    });
    const wrapperWithEndTime = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        end: maintenanceEndDateTime,
      },
    });

    expect(
      wrapperWithoutEndTime
        .find({ "data-test": "maintenance page" })
        .childAt(0)
        .prop("scheduledRemovalDayAndTimeText")
    ).toBeNull();

    expect(
      wrapperWithEndTime
        .find({ "data-test": "maintenance page" })
        .childAt(0)
        .prop("scheduledRemovalDayAndTimeText")
    ).toEqual(maintenanceEndDateTime.toLocaleString(DateTime.DATETIME_FULL));
  });

  it("renders MaintenanceTakeover when current time is between maintenanceStart and maintenanceEnd", () => {
    mockRouter.pathname = "/";

    const wrapperInMaintenanceWindow = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        // Started an hour ago
        start: DateTime.local().minus({ hours: 1 }).toISO(),
        // Ends in an hour
        end: DateTime.local().plus({ hours: 1 }).toISO(),
      },
    });

    const wrapperNotInMaintenanceWindow = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        // Started 2 hours ago
        start: DateTime.local().minus({ hours: 1 }).toISO(),
        // Ended an hour ago
        end: DateTime.local().minus({ hours: 1 }).toISO(),
      },
    });

    expect(hasMaintenancePage(wrapperInMaintenanceWindow)).toBe(true);
    expect(hasMaintenancePage(wrapperNotInMaintenanceWindow)).toBe(false);
  });

  it("renders MaintenanceTakeover when current time is after maintenanceStart and maintenanceEnd is not set", () => {
    mockRouter.pathname = "/";

    const wrapperInMaintenanceWindow = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        // Started an hour ago
        start: DateTime.local().minus({ hours: 1 }).toISO(),
      },
    });

    const wrapperNotInMaintenanceWindow = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        // Starts in one hour
        start: DateTime.local().plus({ hours: 1 }).toISO(),
      },
    });

    expect(hasMaintenancePage(wrapperInMaintenanceWindow)).toBe(true);
    expect(hasMaintenancePage(wrapperNotInMaintenanceWindow)).toBe(false);
  });

  it("renders MaintenanceTakeover when current time is before maintenanceEnd and maintenanceStart is not set", () => {
    mockRouter.pathname = "/";

    const wrapperInMaintenanceWindow = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        // Ends in an hour
        end: DateTime.local().plus({ hours: 1 }).toISO(),
      },
    });

    const wrapperNotInMaintenanceWindow = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        // Ended an hour ago
        end: DateTime.local().minus({ hours: 1 }).toISO(),
      },
    });

    expect(hasMaintenancePage(wrapperInMaintenanceWindow)).toBe(true);
    expect(hasMaintenancePage(wrapperNotInMaintenanceWindow)).toBe(false);
  });

  it("bypasses MaintenanceTakeover when noMaintenance feature flag is present", () => {
    process.env.featureFlags = {
      noMaintenance: true,
      pfmlTerriyay: true,
    };
    mockRouter.pathname = "/login";

    const wrapper = render({
      maintenance: {
        ...maintenance,
        enabled: true,
        options: {
          page_routes: ["/login"],
        },
      },
    });

    expect(hasMaintenancePage(wrapper)).toBe(false);
  });

  it("sets errors prop on ErrorsSummary", () => {
    let appLogic;
    testHook(() => {
      appLogic = useAppLogic();
    });

    const wrapper = render({ appLogic, maintenance });

    expect(wrapper.find("ErrorsSummary").prop("errors")).toBe(
      appLogic.appErrors
    );
  });
});
