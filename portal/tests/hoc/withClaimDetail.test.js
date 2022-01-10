import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../src/models/ClaimDetail";
import Payments from "../../src/pages/applications/status/payments";
import Status from "../../src/pages/applications/status/index";
import { renderPage } from "../test-utils";
import { screen } from "@testing-library/react";

describe("withClaimDetail", () => {
  const setupHelper =
    (claimDetailAttrs, appErrors = new AppErrorInfoCollection()) =>
    (appLogicHook) => {
      appLogicHook.claims.claimDetail = claimDetailAttrs
        ? new ClaimDetail(claimDetailAttrs)
        : null;
      appLogicHook.claims.loadClaimDetail = jest.fn();
      appLogicHook.appErrors = appErrors;
    };

  const statusTabs = [
    {
      statusTabName: "status",
      statusTabComponent: Status,
    },
    {
      statusTabName: "payments",
      statusTabComponent: Payments,
    },
  ];

  const defaultProps = {
    query: { absence_id: "mock-absence-case-id" },
  };

  it.each(statusTabs)(
    "$statusTabName tab redirects to 404 if no absence case ID",
    ({ statusTabComponent }) => {
      renderPage(
        statusTabComponent,
        {
          addCustomSetup: setupHelper(),
        },
        { query: {} }
      );

      const pageNotFoundHeading = screen.getByRole("heading", {
        name: /Page not found/,
      });
      expect(pageNotFoundHeading).toBeInTheDocument();
    }
  );

  it.each(statusTabs)(
    "$statusTabName tab only renders the back button if non-DocumentsLoadErrors exists",
    ({ statusTabComponent }) => {
      renderPage(
        statusTabComponent,
        {
          addCustomSetup: (appLogicHook) => {
            appLogicHook.claims.loadClaimDetail = jest.fn();
            appLogicHook.appErrors = new AppErrorInfoCollection([
              new AppErrorInfo(),
            ]);
          },
        },
        defaultProps
      );

      expect(
        screen.getByRole("link", { name: "Back to your applications" })
      ).toBeInTheDocument();
    }
  );

  it.each(statusTabs)(
    "$statusTabName tab shows a spinner if there is no claim detail",
    ({ statusTabComponent }) => {
      renderPage(
        statusTabComponent,
        {
          addCustomSetup: setupHelper(),
        },
        defaultProps
      );

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    }
  );
});
