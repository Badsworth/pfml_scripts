import { screen, waitFor } from "@testing-library/react";
import { Find } from "../../../src/pages/applications/find";
import { renderPage } from "../../test-utils";
import userEvent from "@testing-library/user-event";

describe("Find", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      channelSwitching: true,
    };
  });

  it("renders page not found when feature flag isn't enabled", () => {
    process.env.featureFlags = { channelSwitching: false };
    renderPage(Find);

    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  it("renders the page", () => {
    const { container } = renderPage(Find);
    expect(container).toMatchSnapshot();
  });

  it("associates application when user clicks submit", async () => {
    const associateMock = jest.fn();
    renderPage(Find, {
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.associate = associateMock;
      },
    });

    userEvent.type(
      screen.getByRole("textbox", { name: /social security/i }),
      "1234"
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /application id/i }),
      "NTN-111-ABS-01"
    );
    userEvent.click(screen.getByRole("button", { name: "Continue" }));

    await waitFor(() => {
      expect(associateMock).toHaveBeenCalledWith({
        absence_id: "NTN-111-ABS-01",
        tax_identifier_last4: "1234",
      });
    });
  });
});
