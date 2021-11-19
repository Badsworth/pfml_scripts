import BondingLeaveAttestation from "../../../src/pages/applications/bonding-leave-attestation";
import { mockRouter } from "next/router";
import { renderPage } from "../../test-utils";
import { screen } from "@testing-library/react";
import { setupBenefitsApplications } from "../../test-utils/helpers";

describe("BondingLeaveAttestation", () => {
  mockRouter.pathname = "/applications/bonding-leave-attestation";
  it("renders the page", () => {
    const { container } = renderPage(
      BondingLeaveAttestation,
      {
        addCustomSetup: (appLogicHook) => {
          setupBenefitsApplications(appLogicHook);
        },
      },
      { query: { claim_id: "mock_application_id" } }
    );
    expect(container).toMatchSnapshot();
    expect(
      screen.getByText(/Confirm that you are an eligible parent/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "I understand and agree" })
    ).toBeInTheDocument();
  });
});
