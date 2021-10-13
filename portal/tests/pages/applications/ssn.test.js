import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import Ssn from "../../../src/pages/applications/ssn";
import { renderPage } from "../../test-utils";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (claimAttrs = {}) => {
  const claim = new BenefitsApplication({
    application_id: "mock_application_id",
    ...claimAttrs,
  });

  return renderPage(
    Ssn,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("Ssn", () => {
  it("renders the form", () => {
    const { container } = setup({
      // API returns the tax_identifier with only the last 4 digits
      tax_identifier: "*****1234",
    });
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when the form is submitted", async () => {
    setup({
      tax_identifier: "*****1234",
    });

    // Existing data
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        tax_identifier: "*****1234",
      });
    });

    // New changes
    userEvent.type(
      screen.getByRole("textbox", {
        name: "What’s your Social Security Number? Don’t have a Social Security Number? Use your Individual Taxpayer Identification Number (ITIN).",
      }),
      "123-12-3123"
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        tax_identifier: "123-12-3123",
      });
    });
  });
});
