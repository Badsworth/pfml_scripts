import { screen, waitFor } from "@testing-library/react";
import ClaimDetail from "../../src/models/ClaimDetail";
import React from "react";
import { renderPage } from "../test-utils";
import withClaimDetail from "../../src/hoc/withClaimDetail";

const mockAbsenceId = "mock-absence-id";
const mockPageContent = "Change request is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup, query } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      ClaimDetail: {props.claim_detail.fineos_absence_id}
    </div>
  );
  const WrappedComponent = withClaimDetail(PageComponent);

  renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        absence_id: mockAbsenceId,
        ...(query || {}),
      },
    }
  );
}

describe(withClaimDetail, () => {
  it("shows spinner when loading claim detail state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.claims.isLoadingClaimDetail = true;
      },
    });

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("shows Page Not Found when absence id isn't found", () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.claims.claimDetail = new ClaimDetail({
          application_id: "application-id",
          fineos_absence_id: "NTN-0",
        });
      },
      query: { absence_id: "" },
    });

    expect(
      screen.getByRole("heading", { name: "Page not found" })
    ).toBeInTheDocument();
  });

  it("requires user to be logged in", async () => {
    let spy;

    setup({
      addCustomSetup: (appLogic) => {
        appLogic.claims.claimDetail = new ClaimDetail({
          application_id: "application-id",
          fineos_absence_id: "NTN-0",
        });
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page when claim detail state is loaded", async () => {
    const mockClaimDetail = new ClaimDetail({
      application_id: "application-id",
      fineos_absence_id: "NTN-0",
    });
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.claims.claimDetail = mockClaimDetail;
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    expect(
      await screen.findByText(mockClaimDetail.fineos_absence_id, {
        exact: false,
      })
    ).toBeInTheDocument();
  });
});
