import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import TaxWithholding from "../../../src/pages/applications/tax-withholding";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = () => {
  const claim = new MockBenefitsApplicationBuilder().part1Complete().create();
  let submitTaxPreferenceSpy;

  const utils = renderPage(
    TaxWithholding,
    {
      addCustomSetup: (appLogic) => {
        submitTaxPreferenceSpy = jest.spyOn(
          appLogic.benefitsApplications,
          "submitTaxWithholdingPreference"
        );
        setupBenefitsApplications(appLogic, [claim]);
      },
    },
    {
      query: { claim_id: claim.application_id },
    }
  );
  return {
    submitTaxPreferenceSpy,
    ...utils,
  };
};

describe("TaxWithholding", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("displays addl explanation information for the user", () => {
    setup();
    expect(screen.getByText("Tax withholding")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "tax professional" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "(833) 344‑7365" })
    ).toBeInTheDocument();
  });

  it("user can click one of two radio options for tax selections", () => {
    setup();
    const yesRadio = screen.getByRole("radio", {
      name: "Yes, withhold state and federal taxes",
    });
    const noRadio = screen.getByRole("radio", {
      name: "No, don’t withhold state and federal taxes",
    });
    userEvent.click(noRadio);
    expect(noRadio).toBeChecked();
    expect(yesRadio).not.toBeChecked();
  });

  it("submits user selections on click", async () => {
    const { submitTaxPreferenceSpy } = setup();
    userEvent.click(
      screen.getByRole("radio", {
        name: "Yes, withhold state and federal taxes",
      })
    );
    userEvent.click(
      screen.getByRole("button", { name: "Submit tax withholding preference" })
    );

    await waitFor(() => {
      expect(submitTaxPreferenceSpy).toHaveBeenCalledWith(
        "mock_application_id",
        {
          is_withholding_tax: true,
        }
      );
    });
  });
});
