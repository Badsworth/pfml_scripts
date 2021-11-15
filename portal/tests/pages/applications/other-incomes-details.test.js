import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../../src/models/OtherIncome";
import { screen, waitFor } from "@testing-library/react";

import OtherIncomesDetails from "../../../src/pages/applications/other-incomes-details";
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
    OtherIncomesDetails,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

const incomeData = {
  income_type: OtherIncomeType.ssdi,
  income_start_date: "2021-03-01",
  income_end_date: "2021-04-01",
  income_amount_dollars: 100,
  income_amount_frequency: OtherIncomeFrequency.monthly,
  other_income_id: null,
};

const setIncomeFields = (income) => {
  userEvent.click(
    screen.getByRole("radio", { name: "Social Security Disability Insurance" })
  );
  const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
    name: "Month",
  });
  const [startDayInput, endDayInput] = screen.getAllByRole("textbox", {
    name: "Day",
  });
  const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
    name: "Year",
  });
  const [startYear, startMonth, startDay] = income.income_start_date.split("-");
  const [endYear, endMonth, endDay] = income.income_end_date.split("-");

  userEvent.type(startDayInput, startDay);
  userEvent.type(startMonthInput, startMonth);
  userEvent.type(startYearInput, startYear);
  userEvent.type(endDayInput, endDay);
  userEvent.type(endMonthInput, endMonth);
  userEvent.type(endYearInput, endYear);

  userEvent.type(
    screen.getByRole("textbox", { name: "Amount" }),
    income.income_amount_dollars.toString()
  );
  userEvent.selectOptions(screen.getByRole("combobox", { name: "Frequency" }), [
    income.income_amount_frequency.toString(),
  ]);
};

const clickFirstRemoveButton = () => {
  const removeButtons = screen.getAllByRole("button", {
    name: "Remove income",
  });
  userEvent.click(removeButtons[0]);
};

const clickAddIncomeButton = () => {
  userEvent.click(screen.getByRole("button", { name: "Add another income" }));
};

const createClaimWithIncomes = () =>
  new MockBenefitsApplicationBuilder()
    .continuous()
    .otherIncome([
      {
        income_amount_dollars: 500,
        income_amount_frequency: OtherIncomeFrequency.weekly,
        income_end_date: "2021-02-01",
        income_start_date: "2021-01-01",
        income_type: OtherIncomeType.unemployment,
      },
      {
        income_amount_dollars: 700,
        income_amount_frequency: OtherIncomeFrequency.monthly,
        income_end_date: "2021-02-05",
        income_start_date: "2021-01-05",
        income_type: OtherIncomeType.jonesAct,
      },
    ])
    .create();

describe("OtherIncomesDetails", () => {
  describe("when the user's claim has no other incomes", () => {
    it("renders the page", () => {
      const { container } = setup();
      expect(container).toMatchSnapshot();
    });

    it("adds a blank entry so a card is rendered", () => {
      setup();
      const entries = screen.getByRole("group", { name: "Income 1" });

      expect(entries).toBeInTheDocument();
    });

    it("calls claims.update with new incomes data when user clicks continue", async () => {
      setup();

      setIncomeFields(incomeData);

      const entries = screen.getByRole("group", { name: "Income 1" });
      expect(entries).toBeInTheDocument();
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          other_incomes: [incomeData],
        });
      });
    });

    it("adds an empty income when the user clicks Add Another Income", () => {
      setup();

      setIncomeFields(incomeData);
      clickAddIncomeButton();

      const entries = screen.getAllByRole("group", { name: /Income/ });
      expect(entries).toHaveLength(2);
    });

    it("removes an income when the user clicks Remove Income", () => {
      setup();

      setIncomeFields(incomeData);

      clickAddIncomeButton();
      const entries = screen.getAllByRole("group", { name: /Income/ });
      expect(entries).toHaveLength(2);

      clickFirstRemoveButton();

      expect(screen.getByRole("group", { name: /Income/ })).toBeInTheDocument();
    });
  });

  describe("when the user's claim has other incomes", () => {
    it("renders the page", () => {
      const claimWithIncomes = createClaimWithIncomes();
      const { container } = setup(claimWithIncomes);
      expect(container).toMatchSnapshot();
    });

    it("adds another income when the user clicks 'Add another'", async () => {
      const claimWithIncomes = createClaimWithIncomes();
      setup(claimWithIncomes);

      clickAddIncomeButton();

      expect(screen.getAllByRole("group", { name: /Income/ }).length).toEqual(
        3
      );

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          other_incomes: [...claimWithIncomes.other_incomes, new OtherIncome()],
        });
      });
    });

    it("calls claims.update when user clicks continue", async () => {
      const claimWithIncomes = createClaimWithIncomes();
      setup(claimWithIncomes);
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          other_incomes: claimWithIncomes.other_incomes,
        });
      });
    });

    describe("when the user clicks 'Remove'", () => {
      it("removes the income", async () => {
        const claimWithIncomes = createClaimWithIncomes();
        setup(claimWithIncomes);
        clickFirstRemoveButton();
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        await waitFor(() => {
          expect(updateClaim).toHaveBeenCalledTimes(1);
        });
      });
    });

    it("Unknown is excluded as an income type option", () => {
      setup();
      expect(screen.getAllByRole("radio")).toHaveLength(
        Object.keys(OtherIncomeType).length - 1
      );
      expect(
        screen.queryByRole("radio", { name: "Unknown" })
      ).not.toBeInTheDocument();
    });
  });
});
