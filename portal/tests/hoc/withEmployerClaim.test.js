import { screen, waitFor } from "@testing-library/react";
import EmployerClaimReview from "../../src/models/EmployerClaimReview";
import React from "react";
import { renderPage } from "../test-utils";
import withEmployerClaim from "../../src/hoc/withEmployerClaim";

const mockAbsenceId = "NTN-111-ABS-01";
const mockPageContent = "Claim is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup, query } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Application: {props.claim?.fineos_absence_id}
    </div>
  );
  const WrappedComponent = withEmployerClaim(PageComponent);

  return renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        absence_id: mockAbsenceId,
        ...query,
      },
    }
  );
}

describe("withEmployerClaim", () => {
  it("shows spinner when loading claim state", async () => {
    setup();

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("shows Page Not Found when absence ID isn't found", () => {
    setup({
      query: {
        absence_id: "",
      },
    });

    expect(
      screen.getByRole("heading", { name: "Page not found" })
    ).toBeInTheDocument();
  });

  it("requires user to be logged in", async () => {
    let spy;

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page when claim state is loaded", async () => {
    const mockClaim = new EmployerClaimReview({
      absence_periods: [],
      fineos_absence_id: mockAbsenceId,
    });

    setup({
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = mockClaim;
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the claim as a prop to our page component:
    expect(
      await screen.findByText(mockClaim.fineos_absence_id, { exact: false })
    ).toBeInTheDocument();
  });
});
