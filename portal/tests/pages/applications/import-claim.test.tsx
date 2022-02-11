import { screen, waitFor } from "@testing-library/react";
import ImportClaim from "../../../src/pages/applications/import-claim";
import { renderPage } from "../../test-utils";
import userEvent from "@testing-library/user-event";

describe("ImportClaim", () => {
  beforeEach(() => {
    process.env.featureFlags = JSON.stringify({
      channelSwitching: true,
    });
  });

  it("renders page not found when feature flag isn't enabled", () => {
    process.env.featureFlags = JSON.stringify({ channelSwitching: false });
    renderPage(ImportClaim);

    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  it("renders the page", () => {
    const { container } = renderPage(ImportClaim);
    expect(container).toMatchSnapshot();
  });

  it("associates application when user clicks submit", async () => {
    const associateMock = jest.fn();
    renderPage(ImportClaim, {
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.associate = associateMock;
      },
    });

    userEvent.type(
      screen.getByRole("textbox", { name: /social security/i }),
      "123456789"
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /application id/i }),
      "NTN-111-ABS-01"
    );
    expect(
      screen.queryByText("Submitting… Do not refresh or go back")
    ).not.toBeInTheDocument();
    userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(
      screen.getByText("Submitting… Do not refresh or go back")
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(associateMock).toHaveBeenCalledWith({
        absence_case_id: "NTN-111-ABS-01",
        tax_identifier: "123-45-6789",
      });
    });
  });
});
