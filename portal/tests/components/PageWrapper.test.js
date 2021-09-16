import { render, screen } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { DateTime } from "luxon";
import Flag from "../../../portal/src/models/Flag";
import PageWrapper from "../../src/components/PageWrapper";
import React from "react";
import User from "../../src/models/User";
import { mockRouter } from "next/router";
import useAppLogic from "../../src/hooks/useAppLogic";

// see https://github.com/vercel/next.js/issues/5416
// jest.mock("next/dynamic", () => () => (_props) => null);
jest.mock("next/dynamic", () => () => {
  const MaintenanceTakeover =
    // eslint-disable-next-line global-require
    require("../../src/components/MaintenanceTakeover").default;

  return (props) => <MaintenanceTakeover {...props} />;
});
jest.mock("react-helmet", () => {
  // Render <title> directly in document.body so we can assert its value
  return { Helmet: ({ children }) => children };
});

const PageWrapperWithAppLogic = ({
  // eslint-disable-next-line react/prop-types
  addAppLogicMocks = (appLogic) => {},
  ...props
}) => {
  const appLogic = useAppLogic();
  appLogic.users.user = new User({ consented_to_data_sharing: true });

  addAppLogicMocks(appLogic);

  return (
    <PageWrapper
      appLogic={appLogic}
      children={<div>Page</div>}
      maintenance={new Flag()}
      {...props}
    />
  );
};

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

    const { container } = render(<PageWrapperWithAppLogic />);

    expect(container.firstChild).toMatchInlineSnapshot(`
          <code>
            Hello world (◕‿◕)
          </code>
        `);
  });

  it("sets description meta tag", () => {
    const { container } = render(<PageWrapperWithAppLogic />);
    // meta element
    expect(container.querySelector("meta")).toMatchSnapshot();
  });

  it("renders the Header", () => {
    render(<PageWrapperWithAppLogic />);

    expect(screen.getByTestId("Header")).toBeInTheDocument();
  });

  it("renders Spinner when isLoading is true", () => {
    const { container } = render(<PageWrapperWithAppLogic isLoading={true} />);
    expect(container.querySelector("#page")).toMatchSnapshot();
  });

  it("renders the children as the page's body", () => {
    const { container } = render(<PageWrapperWithAppLogic />);

    expect(container.querySelector("#page")).toMatchSnapshot();
  });

  it("renders MaintenanceTakeover when maintenancePageRoutes includes the current page's route and no start/end time is set", () => {
    mockRouter.pathname = "/login";

    const maintenanceProp = new Flag({
      enabled: true,
      options: {
        page_routes: ["/login"],
      },
    });
    render(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);

    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();
  });

  it("renders MaintenanceTakeover when maintenancePageRoutes includes a wildcard matching the current page's route", () => {
    // Doesn't render for a page that doesn't match the wildcard
    mockRouter.pathname = "/foo";
    const maintenanceProp = new Flag({
      enabled: true,
      options: {
        page_routes: ["/employers/*"],
      },
    });
    const { rerender } = render(
      <PageWrapperWithAppLogic maintenance={maintenanceProp} />
    );
    expect(screen.queryByTestId("maintenance page")).toBeNull();

    // Matches base pathname
    mockRouter.pathname = "/employers/";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);

    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();

    // Matches sub-pages
    mockRouter.pathname = "/employers/create-account";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);

    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();
  });

  it("renders MaintenanceTakeover on all routes when 'page_routes' is omitted from 'options' in the 'maintenance' feature flag definition", () => {
    // Test random page 1
    mockRouter.pathname = "/applications/";

    const maintenanceProp = new Flag({
      enabled: true,
      options: {},
    });
    const { rerender } = render(
      <PageWrapperWithAppLogic maintenance={maintenanceProp} />
    );
    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();

    // Test random page 2
    mockRouter.pathname = "/employers/";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);
    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();

    // Test random sub-page
    mockRouter.pathname = "/employers/create-account";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);
    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();
  });

  it.skip("renders MaintenanceTakeover with localized start time when maintenanceStart is set", () => {
    mockRouter.pathname = "/";
    // Started an hour ago
    const maintenanceStartDateTime = DateTime.local().minus({ hours: 1 });

    const maintenanceWithoutStartTime = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
    });

    const maintenanceWithStartTime = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      start: maintenanceStartDateTime.toISO(),
    });

    const { rerender } = render(
      <PageWrapperWithAppLogic maintenance={maintenanceWithStartTime} />
    );

    expect(
      screen.getByText(
        maintenanceStartDateTime.toLocaleString(DateTime.DATETIME_FULL)
      )
    ).toBeInTheDocument();

    expect(
      wrapperWithStartTime
        .find({ "data-test": "maintenance page" })
        .childAt(0)
        .prop("maintenanceStartTime")
    ).toEqual(maintenanceStartDateTime.toLocaleString(DateTime.DATETIME_FULL));
  });

  it.skip("renders MaintenanceTakeover with localized end time when maintenanceEnd is set", () => {
    mockRouter.pathname = "/";
    // Ends in an hour
    const maintenanceEndDateTime = DateTime.local().plus({ hours: 1 });

    const wrapperWithoutEndTime = render({
      maintenance: new Flag({
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
      }),
    });

    const wrapperWithEndTime = render({
      maintenance: new Flag({
        enabled: true,
        options: {
          page_routes: ["/*"],
        },
        end: maintenanceEndDateTime.toISO(),
      }),
    });

    expect(
      wrapperWithoutEndTime
        .find({ "data-test": "maintenance page" })
        .childAt(0)
        .prop("maintenanceEndTime")
    ).toBeNull();

    expect(
      wrapperWithEndTime
        .find({ "data-test": "maintenance page" })
        .childAt(0)
        .prop("maintenanceEndTime")
    ).toEqual(maintenanceEndDateTime.toLocaleString(DateTime.DATETIME_FULL));
  });

  it("renders MaintenanceTakeover when current time is between maintenanceStart and maintenanceEnd", () => {
    mockRouter.pathname = "/";

    const maintenanceInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Started 1 hour ago
      start: DateTime.local().minus({ hours: 1 }).toISO(),
      // Ends in 1 hour
      end: DateTime.local().plus({ hours: 1 }).toISO(),
    });

    const maintenanceNotInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Started 2 hours ago
      start: DateTime.local().minus({ hours: 2 }).toISO(),
      // Ended 1 hour ago
      end: DateTime.local().minus({ hours: 1 }).toISO(),
    });

    const { rerender } = render(
      <PageWrapperWithAppLogic maintenance={maintenanceInMaintenanceWindow} />
    );
    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();
    rerender(
      <PageWrapperWithAppLogic
        maintenance={maintenanceNotInMaintenanceWindow}
      />
    );
    expect(screen.queryByTestId("maintenance page")).toBeNull();
  });

  it("renders MaintenanceTakeover when current time is after maintenanceStart and maintenanceEnd is not set", () => {
    mockRouter.pathname = "/";

    const maintenanceInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Started 1 hour ago
      start: DateTime.local().minus({ hours: 1 }).toISO(),
    });

    render(
      <PageWrapperWithAppLogic maintenance={maintenanceInMaintenanceWindow} />
    );
    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();
  });

  it("renders MaintenanceTakeover when current time is before maintenanceEnd and maintenanceStart is not set", () => {
    mockRouter.pathname = "/";

    const maintenanceInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Ends in 1 hour
      end: DateTime.local().plus({ hours: 1 }).toISO(),
    });

    render(
      <PageWrapperWithAppLogic maintenance={maintenanceInMaintenanceWindow} />
    );
    expect(screen.getByTestId("maintenance page")).toBeInTheDocument();
  });

  it("bypasses MaintenanceTakeover when noMaintenance feature flag is present", () => {
    process.env.featureFlags = {
      noMaintenance: true,
      pfmlTerriyay: true,
    };
    mockRouter.pathname = "/login";

    const maintenanceProp = new Flag({
      enabled: true,
      options: {
        page_routes: ["/login"],
      },
    });

    render(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);
    expect(screen.queryByTestId("maintenance page")).toBeNull();
  });

  it("renders error messages when there is app error", () => {
    let appLogic;
    render(
      <PageWrapperWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);
        }}
      />
    );

    expect(
      screen.getByText(
        "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"
      )
    ).toBeInTheDocument();
  });
});
