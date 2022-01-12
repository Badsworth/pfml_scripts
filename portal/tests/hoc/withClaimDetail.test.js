import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../src/models/ClaimDetail";
import { renderPage } from "../test-utils";
import { screen } from "@testing-library/react";
import withClaimDetail from "../../src/hoc/withClaimDetail";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaimDetail", () => {
  const setupHelper =
    (
      isLoading = false,
      claimDetailAttrs,
      appErrors = new AppErrorInfoCollection()
    ) =>
    (appLogicHook) => {
      appLogicHook.claims.claimDetail = claimDetailAttrs
        ? new ClaimDetail(claimDetailAttrs)
        : null;
      appLogicHook.claims.loadClaimDetail = jest.fn();
      appLogicHook.appErrors = appErrors;
      appLogicHook.claims.isLoadingClaimDetail = isLoading;
    };

  const PageComponent = (props) => (
    <div data-testid="page-component">
      This page contains claim detail Application: {props.claim?.application_id}
    </div>
  );

  const WrappedComponent = withClaimDetail(PageComponent);

  const defaultProps = {
    query: { absence_id: "mock-absence-case-id" },
  };

  it("redirects to 404 if no absence case ID", () => {
    renderPage(
      WrappedComponent,
      {
        addCustomSetup: setupHelper(),
      },
      { query: {} }
    );

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });

  it("shows a spinner if there is no claim detail", () => {
    renderPage(
      WrappedComponent,
      {
        addCustomSetup: setupHelper(true),
      },
      {
        ...defaultProps,
      }
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows a spinner if there is no claim detail", () => {
    renderPage(
      WrappedComponent,
      {
        addCustomSetup: setupHelper(true),
      },
      {
        ...defaultProps,
      }
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders the page when application state is loaded", () => {
    renderPage(
      WrappedComponent,
      {
        addCustomSetup: setupHelper(),
      },
      {
        ...defaultProps,
      }
    );

    expect(screen.getByTestId("page-component")).toBeInTheDocument();
  });
});
