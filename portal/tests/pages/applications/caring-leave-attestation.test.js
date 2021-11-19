import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import CaringLeaveAttestation from "../../../src/pages/applications/caring-leave-attestation";
import { screen } from "@testing-library/react";
import { setupBenefitsApplications } from "../../test-utils/helpers";

jest.mock("../../../src/hooks/useLoggedInRedirect");
const claim = new MockBenefitsApplicationBuilder()
  .part1Complete()
  .caringLeaveReason()
  .create();

describe("CaringLeaveAttestation", () => {
  it("renders the page", () => {
    const { container } = renderPage(
      CaringLeaveAttestation,
      {
        addCustomSetup: (hook) => setupBenefitsApplications(hook, [claim]),
      },
      { query: { claim_id: "mock_application_id" } }
    );

    expect(container).toMatchSnapshot();
    expect(
      screen.getByText(/Confirm that you are an eligible caregiver/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "I understand and agree" })
    ).toBeInTheDocument();
  });
});
