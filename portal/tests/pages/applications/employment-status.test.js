import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { EmploymentStatus } from "../../../src/models/BenefitsApplication";
import EmploymentStatusPage from "../../../src/pages/applications/employment-status";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const testFein = "123456789";

const setup = (claim) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder().create();
  }
  return renderPage(
    EmploymentStatusPage,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("EmploymentStatusPage", () => {
  describe("when claimantShowEmploymentStatus feature flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowEmploymentStatus: false,
      };
    });

    it("renders the page without the employment status field", () => {
      const { container } = setup();
      expect(container).toMatchSnapshot();
    });

    it("submits status and FEIN", async () => {
      setup();

      userEvent.type(
        screen.getByRole("textbox", {
          name: "What is your employer’s Employer Identification Number (EIN)? This number is 9 digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W‑2 or 1099‑MISC. Ask your employer if you need help getting this information.",
        }),
        testFein
      );
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employment_status: EmploymentStatus.employed,
          employer_fein: "12-3456789",
        });
      });
    });
  });

  describe("when claimantShowEmploymentStatus feature flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowEmploymentStatus: true,
      };
    });

    it("renders the page with the employment status field", () => {
      const { container } = setup();
      expect(container).toMatchSnapshot();
    });

    it("when user selects employed in MA as their employment status submits status and FEIN", async () => {
      setup();
      userEvent.click(
        screen.getByRole("radio", { name: "I’m employed in Massachusetts" })
      );

      userEvent.type(
        screen.getByRole("textbox", {
          name: "What is your employer’s Employer Identification Number (EIN)? This number is 9 digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W‑2 or 1099‑MISC. Ask your employer if you need help getting this information.",
        }),
        testFein
      );
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employment_status: EmploymentStatus.employed,
          employer_fein: "12-3456789",
        });
      });
    });

    it("when user selects self-employed as their employment status, hides FEIN question", () => {
      setup();
      userEvent.click(screen.getByRole("radio", { name: "I’m self-employed" }));
      expect(
        screen.queryByRole("textbox", {
          name: "What is your employer’s Employer Identification Number (EIN)? This number is 9 digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W‑2 or 1099‑MISC. Ask your employer if you need help getting this information.",
        })
      ).not.toBeInTheDocument();
    });

    it("when user selects self-employed as their employment status, submits status and empty FEIN", async () => {
      setup();
      userEvent.click(screen.getByRole("radio", { name: "I’m self-employed" }));
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employment_status: EmploymentStatus.selfEmployed,
          employer_fein: null,
        });
      });
    });

    it("when user selects unemployed, hides FEIN question", () => {
      setup();
      userEvent.click(screen.getByRole("radio", { name: "I’m unemployed" }));
      expect(
        screen.queryByRole("textbox", {
          name: "What is your employer’s Employer Identification Number (EIN)? This number is 9 digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W‑2 or 1099‑MISC. Ask your employer if you need help getting this information.",
        })
      ).not.toBeInTheDocument();
    });

    it("when claim has existing employment status, submits status and FEIN without changing fields", async () => {
      const claim = new MockBenefitsApplicationBuilder().employed().create();
      setup(claim);

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employment_status: EmploymentStatus.employed,
          employer_fein: "12-3456789",
        });
      });
    });
  });
});
