import {
  MockClaimBuilder,
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
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomesDetails", () => {
  let appLogic, claim, submitForm, wrapper;

  describe("when the user's claim has other income sources", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder()
        .continuous()
        .otherIncome([
          {
            income_amount_dollars: 500,
            income_amount_frequency: OtherIncomeFrequency.weekly,
            income_end_date: "2021-02-01",
            income_start_date: "2021-01-01",
            income_type: OtherIncomeType.ssdi,
          },
          {
            income_amount_dollars: 700,
            income_amount_frequency: OtherIncomeFrequency.monthly,
            income_end_date: "2021-02-06",
            income_start_date: "2021-01-06",
            income_type: OtherIncomeType.jonesAct,
          },
        ])
        .create();

      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: claim,
      }));
      submitForm = simulateEvents(wrapper).submitForm;
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls claims.update", async () => {
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: claim.other_incomes,
          }
        );
      });
    });

    describe("when the user clicks 'Add another'", () => {
      it("adds another entry", async () => {
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
      let removeButton;

      beforeEach(() => {
        removeButton = wrapper
          .find(RepeatableFieldset)
          .dive()
          .find(RepeatableFieldsetCard)
          .first()
          .dive()
          .find("Button");
      });

      describe("and the income isn't saved to the API", () => {
        it("removes the income", async () => {
          appLogic.claims.update.mockImplementationOnce(
            (applicationId, patchData) => {
              expect(applicationId).toBe(claim.application_id);
              expect(patchData.other_incomes).toHaveLength(1);
            }
          );

          await act(async () => {
            await removeButton.simulate("click");
          });
          await submitForm();

          expect(appLogic.otherLeaves.removeOtherIncome).not.toHaveBeenCalled();
          expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
        });
      });

      describe("and the income is saved to the API", () => {
        beforeEach(() => {
          claim.other_incomes[0].other_income_id = "mock-other-income-id-1";
        });

        describe("when the DELETE request succeeds", () => {
          it("removes the income", async () => {
            appLogic.claims.update.mockImplementationOnce(
              (applicationId, patchData) => {
                expect(applicationId).toBe(claim.application_id);
                expect(patchData.other_incomes).toHaveLength(1);
              }
            );

            await act(async () => {
              await removeButton.simulate("click");
            });
            await submitForm();

            expect(appLogic.otherLeaves.removeOtherIncome).toHaveBeenCalled();
            expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
          });
        });

        describe("when the DELETE request fails", () => {
          beforeEach(() => {
            appLogic.otherLeaves.removeOtherIncome.mockImplementationOnce(
              () => false
            );
          });

          it("does not remove the income", async () => {
            appLogic.claims.update.mockImplementationOnce(
              (applicationId, patchData) => {
                expect(applicationId).toBe(claim.application_id);
                expect(patchData.other_incomes).toHaveLength(2);
              }
            );

            await act(async () => {
              await removeButton.simulate("click");
            });
            await submitForm();

            expect(appLogic.otherLeaves.removeOtherIncome).toHaveBeenCalled();
            expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
          });
        });
      });
    });
  });

  describe("when the user's claim does not have other incomes", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().continuous().create();

      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: claim,
      }));
    });

    it("adds a blank entry so a card is rendered", () => {
      const entries = wrapper.find(RepeatableFieldset).prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new OtherIncome());
    });
  });

  describe("when there are validation errors", () => {
    it.todo("updates the formState with other_income_id - see CP-1686");
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
