import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../test-utils";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../../src/models/OtherIncome";
import OtherIncomesDetails, {
  OtherIncomeCard,
} from "../../../src/pages/applications/other-incomes-details";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs) => {
  const claim = new MockBenefitsApplicationBuilder().continuous().create();

  const { appLogic, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
    claimAttrs: claimAttrs || claim,
  });
  const { changeField, click, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    click,
    submitForm,
    wrapper,
  };
};

const incomeData = {
  income_type: OtherIncomeType.ssdi,
  income_start_date: "2021-03-01",
  income_end_date: "2021-04-01",
  income_amount_dollars: 100,
  income_amount_frequency: OtherIncomeFrequency.monthly,
  other_income_id: null,
};

const setIncomeFields = (wrapper, income) => {
  const otherIncomeCard = wrapper
    .find(RepeatableFieldset)
    .dive()
    .find(RepeatableFieldsetCard)
    .first()
    .dive()
    .find("OtherIncomeCard")
    .first()
    .dive();

  const { changeRadioGroup, changeField } = simulateEvents(otherIncomeCard);
  changeRadioGroup("other_incomes[0].income_type", income.income_type);
  changeField("other_incomes[0].income_start_date", income.income_start_date);
  changeField("other_incomes[0].income_end_date", income.income_end_date);
  changeField(
    "other_incomes[0].income_amount_dollars",
    income.income_amount_dollars
  );
  changeField(
    "other_incomes[0].income_amount_frequency",
    income.income_amount_frequency
  );
};

const clickFirstRemoveButton = async (wrapper) => {
  // can't use simulateEvent's .click() here because this is a Child component
  await wrapper
    .find(RepeatableFieldset)
    .dive()
    .find(RepeatableFieldsetCard)
    .first()
    .dive()
    .find("Button")
    .simulate("click");
};

const clickAddIncomeButton = async (wrapper) => {
  await wrapper
    .find(RepeatableFieldset)
    .dive()
    .find({ name: "add-entry-button" })
    .simulate("click");
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
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
    });

    it("adds a blank entry so a card is rendered", () => {
      const { wrapper } = setup();
      const entries = wrapper.find(RepeatableFieldset).prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new OtherIncome());

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
          .length
      ).toEqual(1);
    });

    it("calls claims.update with new incomes data when user clicks continue", async () => {
      const { appLogic, claim, submitForm, wrapper } = setup();

      setIncomeFields(wrapper, incomeData);

      const entries = wrapper.find(RepeatableFieldset).prop("entries");
      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(incomeData);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          other_incomes: [incomeData],
        }
      );
    });

    it("adds an empty income when the user clicks Add Another Income", async () => {
      const { wrapper } = setup();

      setIncomeFields(wrapper, incomeData);
      await clickAddIncomeButton(wrapper);

      const entries = wrapper.find(RepeatableFieldset).prop("entries");
      expect(entries).toHaveLength(2);
      expect(entries).toEqual([incomeData, new OtherIncome()]);

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
      ).toHaveLength(2);
    });

    it("removes an income when the user clicks Remove Income", async () => {
      const { wrapper } = setup();

      setIncomeFields(wrapper, incomeData);

      await clickAddIncomeButton(wrapper);

      await clickFirstRemoveButton(wrapper);

      const entries = wrapper.find(RepeatableFieldset).prop("entries");
      expect(entries).toHaveLength(1);
      expect(entries).toEqual([new OtherIncome()]);

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
      ).toHaveLength(1);
    });
  });

  describe("when the user's claim has other incomes", () => {
    it("renders the page", () => {
      const claimWithIncomes = createClaimWithIncomes();
      const { wrapper } = setup(claimWithIncomes);
      expect(wrapper).toMatchSnapshot();
    });

    it("adds another income when the user clicks 'Add another'", async () => {
      const claimWithIncomes = createClaimWithIncomes();
      const { appLogic, claim, submitForm, wrapper } = setup(claimWithIncomes);

      clickAddIncomeButton(wrapper);

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
          .length
      ).toEqual(3);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          other_incomes: [...claimWithIncomes.other_incomes, new OtherIncome()],
        }
      );
    });

    it("calls claims.update when user clicks continue", async () => {
      const claimWithIncomes = createClaimWithIncomes();
      const { appLogic, claim, submitForm } = setup(claimWithIncomes);
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          other_incomes: claimWithIncomes.other_incomes,
        }
      );
    });

    describe("when the user clicks 'Remove'", () => {
      it("removes the income", async () => {
        const claimWithIncomes = createClaimWithIncomes();
        const { appLogic, submitForm, wrapper } = setup(claimWithIncomes);
        appLogic.benefitsApplications.update.mockImplementationOnce(
          (applicationId, patchData) => {
            expect(applicationId).toBe(claimWithIncomes.application_id);
            expect(patchData.other_incomes).toEqual([
              claimWithIncomes.other_incomes[1],
            ]);
          }
        );

        await clickFirstRemoveButton(wrapper);
        await submitForm();

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);
      });
    });
  });
});

const setupIncomeCard = () => {
  const index = 0;
  const entry = new OtherIncome();
  let getFunctionalInputProps;

  testHook(() => {
    getFunctionalInputProps = useFunctionalInputProps({
      appErrors: new AppErrorInfoCollection(),
      formState: {},
      updateFields: jest.fn(),
    });
  });

  const wrapper = shallow(
    <OtherIncomeCard
      entry={entry}
      index={index}
      getFunctionalInputProps={getFunctionalInputProps}
    />
  );

  return {
    index,
    wrapper,
  };
};

describe("OtherIncomeCard", () => {
  it("renders fields for an OtherIncome instance", () => {
    const { wrapper } = setupIncomeCard();
    expect(wrapper).toMatchSnapshot();
  });

  it("doesn't include Unknown as an income type option", () => {
    const { index, wrapper } = setupIncomeCard();
    const field = wrapper.find({
      name: `other_incomes[${index}].income_type`,
    });

    expect(field.prop("choices")).not.toContainEqual(
      expect.objectContaining({ value: OtherIncomeType.unknown })
    );
  });
});
