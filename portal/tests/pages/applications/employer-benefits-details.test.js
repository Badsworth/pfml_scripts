import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import EmployerBenefitsDetails from "../../../src/pages/applications/employer-benefits-details";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (claim) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder().continuous().create();
  }

  return renderPage(
    EmployerBenefitsDetails,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    {
      query: { claim_id: "mock_application_id" },
    }
  );
};

const benefitData = {
  benefit_type: EmployerBenefitType.shortTermDisability,
  benefit_start_date: "2021-03-01",
  benefit_end_date: "2021-04-01",
  is_full_salary_continuous: false,
  benefit_amount_dollars: 100,
  benefit_amount_frequency: EmployerBenefitFrequency.monthly,
  employer_benefit_id: null,
};

const setBenefitFields = (benefit) => {
  userEvent.click(
    screen.getByRole("radio", {
      name: "Temporary disability insurance Short-term or long-term disability",
    })
  );

  const [startMonth, endMonth] = screen.getAllByRole("textbox", {
    name: "Month",
  });
  const [startDay, endDay] = screen.getAllByRole("textbox", { name: "Day" });
  const [startYear, endYear] = screen.getAllByRole("textbox", {
    name: "Year",
  });
  userEvent.type(startMonth, "3");
  userEvent.type(startDay, "1");
  userEvent.type(startYear, "2021");
  userEvent.type(endMonth, "4");
  userEvent.type(endDay, "1");
  userEvent.type(endYear, "2021");

  userEvent.click(screen.getByRole("radio", { name: "No" }));
  userEvent.type(
    screen.getByRole("textbox", { name: "Amount" }),
    benefit.benefit_amount_dollars.toString()
  );
  userEvent.selectOptions(screen.getByRole("combobox", { name: "Frequency" }), [
    benefit.benefit_amount_frequency,
  ]);
};

const clickFirstRemoveButton = () => {
  const allRemovalButtons = screen.getAllByRole("button", {
    name: "Remove benefit",
  });
  userEvent.click(allRemovalButtons[0]);
};

const clickAddBenefitButton = () => {
  userEvent.click(screen.getByRole("button", { name: "Add another benefit" }));
};

const createClaimWithBenefits = () =>
  new MockBenefitsApplicationBuilder()
    .continuous()
    .employerBenefit([
      {
        benefit_amount_dollars: 500,
        benefit_amount_frequency: EmployerBenefitFrequency.weekly,
        benefit_end_date: "2021-02-01",
        benefit_start_date: "2021-01-01",
        benefit_type: EmployerBenefitType.familyOrMedicalLeave,
        is_full_salary_continuous: true,
      },
      {
        benefit_amount_dollars: 700,
        benefit_amount_frequency: EmployerBenefitFrequency.monthly,
        benefit_end_date: "2021-02-05",
        benefit_start_date: "2021-01-05",
        benefit_type: EmployerBenefitType.permanentDisability,
        is_full_salary_continuous: false,
      },
    ])
    .create();

describe("EmployerBenefitsDetails", () => {
  describe("when the user's claim has no employer benefits", () => {
    it("renders the page", () => {
      const { container } = setup();
      expect(container).toMatchSnapshot();
    });

    it("adds a blank entry so a card is rendered", () => {
      setup();
      const entries = screen.getByTestId("repeatable-fieldset-card");
      expect(entries).toBeInTheDocument();
    });

    it("calls claims.update with new benefits data when user clicks continue", async () => {
      setup();

      setBenefitFields(benefitData);

      const entries = screen.getByTestId("repeatable-fieldset-card");
      expect(entries).toBeInTheDocument();

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employer_benefits: [benefitData],
        });
      });
    });

    it("adds an empty benefit when the user clicks Add Another Benefit", () => {
      setup();
      setBenefitFields(benefitData);
      clickAddBenefitButton();

      const entries = screen.getAllByTestId("repeatable-fieldset-card");
      expect(entries).toHaveLength(2);
    });

    it("removes a benefit when the user clicks Remove Benefit", () => {
      setup();

      setBenefitFields(benefitData);

      clickAddBenefitButton();

      clickFirstRemoveButton();

      const entries = screen.getByTestId("repeatable-fieldset-card");
      expect(entries).toBeInTheDocument();
    });
  });

  describe("when the user's claim has employer benefits", () => {
    it("renders the page", () => {
      const claimWithBenefits = createClaimWithBenefits();
      const { container } = setup(claimWithBenefits);
      expect(container).toMatchSnapshot();
    });

    it("adds another benefit when the user clicks 'Add another'", async () => {
      const claimWithBenefits = createClaimWithBenefits();
      setup(claimWithBenefits);

      clickAddBenefitButton();

      const entries = screen.getAllByTestId("repeatable-fieldset-card");
      expect(entries).toHaveLength(3);

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employer_benefits: [
            ...claimWithBenefits.employer_benefits,
            new EmployerBenefit(),
          ],
        });
      });
    });

    it("calls claims.update when user clicks continue", async () => {
      const claimWithBenefits = createClaimWithBenefits();
      setup(claimWithBenefits);
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employer_benefits: claimWithBenefits.employer_benefits,
        });
      });
    });

    it("when the user clicks 'Remove' removes the benefit", async () => {
      const claimWithBenefits = createClaimWithBenefits();
      setup(claimWithBenefits);

      clickAddBenefitButton();
      clickFirstRemoveButton();

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      // Note we expect call to have first item from claimWithBenefits removed
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          employer_benefits: [
            claimWithBenefits.employer_benefits[1],
            new EmployerBenefit(),
          ],
        });
      });
    });

    it("excludes unknown benefit types from display in the EmployerBenefitCard", () => {
      setup();
      const choiceOptions = screen.getAllByRole("radio");
      expect(choiceOptions).toHaveLength(5); // 3 for benefit type, 2 for salary
      expect(screen.queryByText(/unknown/i)).not.toBeInTheDocument();
    });
  });
});
