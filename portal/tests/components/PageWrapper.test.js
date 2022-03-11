import { render, screen } from "@testing-library/react";
import Flag from "../../src/models/Flag";
import { InternalServerError } from "../../src/errors";
import PageWrapper from "../../src/components/PageWrapper";
import React from "react";
import User from "../../src/models/User";
import dayjs from "dayjs";
import { mockRouter } from "next/router";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("next/dynamic", () => (...args) => {
  if (args[0] && args[0].toString().includes("MaintenanceTakeover")) {
    const MaintenanceTakeover =
      // eslint-disable-next-line global-require
      require("../../src/components/MaintenanceTakeover").default;
    // eslint-disable-next-line react/display-name
    return (props) => <MaintenanceTakeover {...props} />;
  } else if (args[0] && args[0].toString().includes("Footer")) {
    const Footer =
      // eslint-disable-next-line global-require
      require("../../src/components/Footer").default;
    // eslint-disable-next-line react/display-name
    return () => <Footer />;
  } else {
    return () => null;
  }
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
    <PageWrapper appLogic={appLogic} maintenance={new Flag()} {...props}>
      <div>Page</div>
    </PageWrapper>
  );
};

describe("PageWrapper", () => {
  beforeEach(() => {
    // Enable rendering of the site
    process.env.featureFlags = JSON.stringify({
      pfmlTerriyay: true,
    });
  });

  it("doesn't render the site when the 'pfmlTerriyay' feature flag is disabled", () => {
    process.env.featureFlags = JSON.stringify({
      pfmlTerriyay: false,
    });

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
    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders the Header", () => {
    render(<PageWrapperWithAppLogic />);

    expect(screen.getByTestId("Header")).toBeInTheDocument();
  });

  it("renders the Footer", () => {
    render(<PageWrapperWithAppLogic />);

    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("renders Spinner when isLoading is true", () => {
    render(<PageWrapperWithAppLogic isLoading={true} />);
    expect(screen.getByRole("main")).toMatchSnapshot();
  });

  it("renders the children as the page's body", () => {
    render(<PageWrapperWithAppLogic />);

    expect(screen.getByRole("main")).toMatchSnapshot();
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

    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();
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
    expect(
      screen.queryByRole("heading", { name: "We’re undergoing maintenance" })
    ).not.toBeInTheDocument();

    // Matches base pathname
    mockRouter.pathname = "/employers/";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);

    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();

    // Matches sub-pages
    mockRouter.pathname = "/employers/create-account";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);

    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();
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
    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();

    // Test random page 2
    mockRouter.pathname = "/employers/";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);
    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();

    // Test random sub-page
    mockRouter.pathname = "/employers/create-account";
    rerender(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);
    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();
  });

  it("renders MaintenanceTakeover with localized end time when maintenanceEnd is set", () => {
    mockRouter.pathname = "/";
    // Ends in an hour format e.g. 2021-11-12T11:00:04.666-08:00
    const maintenanceEndDateTime = dayjs().add(1, "hour");
    const maintenanceWithoutEndTime = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
    });

    const maintenanceWithEndTime = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      end: maintenanceEndDateTime.toISOString(),
    });

    const { rerender } = render(
      <PageWrapperWithAppLogic maintenance={maintenanceWithoutEndTime} />
    );
    expect(
      screen.queryByText(
        new Intl.DateTimeFormat("default", {
          dateStyle: "long",
          timeStyle: "short",
        }).format(dayjs(maintenanceEndDateTime).toDate())
      )
    ).not.toBeInTheDocument();

    rerender(<PageWrapperWithAppLogic maintenance={maintenanceWithEndTime} />);

    // format e.g. November 12, 2021, 11:00 AM PST
    expect(
      screen.getByText(
        new Intl.DateTimeFormat("default", {
          dateStyle: "long",
          timeStyle: "short",
        }).format(dayjs(maintenanceEndDateTime).toDate())
      )
    ).toBeInTheDocument();
  });

  it("renders MaintenanceTakeover when current time is between maintenanceStart and maintenanceEnd", () => {
    mockRouter.pathname = "/";

    const maintenanceInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Started 1 hour ago
      start: dayjs().subtract(1, "hour").toISOString(),
      // Ends in 1 hour
      end: dayjs().add(1, "hour").toISOString(),
    });

    const maintenanceNotInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Started 2 hours ago
      start: dayjs().subtract(2, "hour").toISOString(),
      // Ended 1 hour ago
      end: dayjs().subtract(1, "hour").toISOString(),
    });

    const { rerender } = render(
      <PageWrapperWithAppLogic maintenance={maintenanceInMaintenanceWindow} />
    );
    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();
    rerender(
      <PageWrapperWithAppLogic
        maintenance={maintenanceNotInMaintenanceWindow}
      />
    );
    expect(
      screen.queryByRole("heading", { name: "We’re undergoing maintenance" })
    ).not.toBeInTheDocument();
  });

  it("renders MaintenanceTakeover when current time is after maintenanceStart and maintenanceEnd is not set", () => {
    mockRouter.pathname = "/";

    const maintenanceInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Started 1 hour ago
      start: dayjs().subtract(1, "hour").toISOString(),
    });

    render(
      <PageWrapperWithAppLogic maintenance={maintenanceInMaintenanceWindow} />
    );
    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();
  });

  it("renders MaintenanceTakeover when current time is before maintenanceEnd and maintenanceStart is not set", () => {
    mockRouter.pathname = "/";

    const maintenanceInMaintenanceWindow = new Flag({
      enabled: true,
      options: {
        page_routes: ["/*"],
      },
      // Ends in 1 hour
      end: dayjs().add(1, "hour").toISOString(),
    });

    render(
      <PageWrapperWithAppLogic maintenance={maintenanceInMaintenanceWindow} />
    );
    expect(
      screen.getByRole("heading", { name: "We’re undergoing maintenance" })
    ).toBeInTheDocument();
  });

  it("bypasses MaintenanceTakeover when noMaintenance feature flag is present", () => {
    process.env.featureFlags = JSON.stringify({
      noMaintenance: true,
      pfmlTerriyay: true,
    });
    mockRouter.pathname = "/login";

    const maintenanceProp = new Flag({
      enabled: true,
      options: {
        page_routes: ["/login"],
      },
    });

    render(<PageWrapperWithAppLogic maintenance={maintenanceProp} />);
    expect(
      screen.queryByRole("heading", { name: "We’re undergoing maintenance" })
    ).not.toBeInTheDocument();
  });

  it("renders error messages when there is app error", () => {
    let appLogic;
    render(
      <PageWrapperWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.errors = [new InternalServerError()];
        }}
      />
    );

    expect(screen.getByText(/unexpected error/)).toBeInTheDocument();
  });
});
