import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../src/models/ClaimDetail";
import { renderPage } from "../test-utils";
import { screen } from "@testing-library/react";
import withClaimDetail from "../../src/hoc/withClaimDetail";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaimDetail", () => {
  const setupHelper =
    (claimDetailAttrs, appErrors = new AppErrorInfoCollection()) =>
    (appLogicHook) => {
      appLogicHook.claims.claimDetail = claimDetailAttrs
        ? new ClaimDetail(claimDetailAttrs)
        : null;
      appLogicHook.claims.loadClaimDetail = jest.fn();
      appLogicHook.appErrors = appErrors;
      appLogicHook.claims.isLoadingClaimDetail = true;
    };

  const PageComponent = (props) => (
    <div>
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
    console.log(WrappedComponent);
    renderPage(
      WrappedComponent,
      {
        addCustomSetup: setupHelper(),
      },
      {
        ...defaultProps,
      }
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });
});
