import { screen, waitFor } from "@testing-library/react";
import Import from "../../../src/pages/applications/import";
import { renderPage } from "../../test-utils";
import userEvent from "@testing-library/user-event";

describe("Import", () => {
  beforeEach(() => {
    process.env.featureFlags = JSON.stringify({
      channelSwitching: true,
    });
  });

  it("renders page not found when feature flag isn't enabled", () => {
    process.env.featureFlags = JSON.stringify({ channelSwitching: false });
    renderPage(Import);

    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  it("renders the page", () => {
    const { container } = renderPage(Import);
    expect(container).toMatchSnapshot();
  });

  it("associates application when user clicks submit", async () => {
    const associateMock = jest.fn();
    renderPage(Import, {
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
    userEvent.click(screen.getByRole("button", { name: "Continue" }));

    await waitFor(() => {
      expect(associateMock).toHaveBeenCalledWith({
        absence_case_id: "NTN-111-ABS-01",
        tax_identifier: "123-45-6789",
      });
    });
  });
});
