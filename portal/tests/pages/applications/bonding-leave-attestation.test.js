import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import BondingLeaveAttestation from "../../../src/pages/applications/bonding-leave-attestation";
import { mockRouter } from "next/router";
import { screen } from "@testing-library/react";

describe("BondingLeaveAttestation", () => {
  mockRouter.pathname = "/applications/bonding-leave-attestation";
  it("renders the page", () => {
    const { container } = renderPage(
      BondingLeaveAttestation,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.load = jest.fn();
          appLogicHook.benefitsApplications.loadAll = jest.fn();
          appLogicHook.benefitsApplications.hasLoadedAll = true;
          appLogicHook.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([
              new MockBenefitsApplicationBuilder().create(),
            ]);
          appLogicHook.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings =
            jest.fn(() => Promise.resolve(true));
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
