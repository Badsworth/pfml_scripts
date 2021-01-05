import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../test-utils";
import OtherIncome, { OtherIncomeType } from "../../../src/models/OtherIncome";
import OtherIncomesDetails, {
  OtherIncomeCard,
} from "../../../src/pages/applications/other-incomes-details";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomesDetails", () => {
  let appLogic, claim, wrapper;

  describe("when the user's claim has other income sources", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().continuous().otherIncome().create();

      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: claim,
      }));
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls claims.update", async () => {
        const { submitForm } = simulateEvents(wrapper);

        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: claim.other_incomes,
          }
        );
      });

      it("calls claims.update with amount string changed to a number", async () => {
        expect.assertions();

        ({ appLogic, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
          claimAttrs: claim,
          render: "mount",
        }));
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("other_incomes[0].income_amount_dollars", "1,000,000");
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: expect.arrayContaining([
              expect.objectContaining({
                income_amount_dollars: 1000000,
              }),
            ]),
          }
        );
      });

      it("calls claims.update with empty amount string changed to null", async () => {
        expect.assertions();

        ({ appLogic, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
          claimAttrs: claim,
          render: "mount",
        }));
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("other_incomes[0].income_amount_dollars", "");
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: expect.arrayContaining([
              expect.objectContaining({
                income_amount_dollars: null,
              }),
            ]),
          }
        );
      });

      it("calls claims.update without coercing an undefined amount to null", async () => {
        expect.assertions();

        delete claim.other_incomes[0].income_amount_dollars;

        ({ appLogic, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
          claimAttrs: claim,
          render: "mount",
        }));
        const { submitForm } = simulateEvents(wrapper);

        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: expect.arrayContaining([
              expect.objectContaining({
                income_amount_dollars: undefined,
              }),
            ]),
          }
        );
      });
    });

    describe("when the user clicks 'Add another'", () => {
      it("adds another entry", async () => {
        const { submitForm } = simulateEvents(wrapper);

        act(() => {
          wrapper.find(RepeatableFieldset).simulate("addClick");
        });

        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: [...claim.other_incomes, new OtherIncome()],
          }
        );
      });
    });

    describe("when the user clicks 'Remove'", () => {
      it("removes the entry", async () => {
        const { submitForm } = simulateEvents(wrapper);

        act(() => {
          wrapper
            .find(RepeatableFieldset)
            .dive()
            .find(RepeatableFieldsetCard)
            .simulate("removeClick");
        });

        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: [],
          }
        );
      });
    });
  });

  describe("when the user's claim does not have employer benefits", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().continuous().create();

      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: claim,
      }));
    });

    it("adds a blank entry so a card is rendered", () => {
      const entries = wrapper.find("RepeatableFieldset").prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new OtherIncome());
    });
  });
});

describe("OtherIncomeCard", () => {
  let wrapper;
  const index = 0;

  beforeEach(() => {
    const entry = new OtherIncome();
    let getFunctionalInputProps;

    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields: jest.fn(),
      });
    });

    wrapper = shallow(
      <OtherIncomeCard
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
      />
    );
  });

  it("renders fields for an OtherIncome instance", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("doesn't include Unknown as a benefit type option", () => {
    const field = wrapper.find({
      name: `other_incomes[${index}].income_type`,
    });

    expect(field.prop("choices")).not.toContainEqual(
      expect.objectContaining({ value: OtherIncomeType.unknown })
    );
  });
});
