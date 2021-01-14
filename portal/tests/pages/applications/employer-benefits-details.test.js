import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import EmployerBenefitDetails, {
  EmployerBenefitCard,
} from "../../../src/pages/applications/employer-benefits-details";
import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefitDetails", () => {
  let appLogic, claim, submitForm, wrapper;

  describe("when the user's claim has employer benefits", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder()
        .continuous()
        .employerBenefit([
          {
            benefit_amount_dollars: 500,
            benefit_amount_frequency: EmployerBenefitFrequency.weekly,
            benefit_end_date: "2021-02-01",
            benefit_start_date: "2021-01-01",
            benefit_type: EmployerBenefitType.familyOrMedicalLeave,
          },
          {
            benefit_amount_dollars: 700,
            benefit_amount_frequency: EmployerBenefitFrequency.monthly,
            benefit_end_date: "2021-02-05",
            benefit_start_date: "2021-01-05",
            benefit_type: EmployerBenefitType.paidLeave,
          },
        ])
        .create();

      ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails, {
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
            employer_benefits: claim.employer_benefits,
          }
        );
      });

      it("calls claims.update with amount string changed to a number", async () => {
        expect.assertions();

        ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails, {
          claimAttrs: claim,
          render: "mount",
        }));
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("employer_benefits[0].benefit_amount_dollars", "1,000,000");
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employer_benefits: expect.arrayContaining([
              expect.objectContaining({
                benefit_amount_dollars: 1000000,
              }),
            ]),
          }
        );
      });

      it("calls claims.update with empty amount string changed to null", async () => {
        expect.assertions();

        ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails, {
          claimAttrs: claim,
          render: "mount",
        }));
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("employer_benefits[0].benefit_amount_dollars", "");
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employer_benefits: expect.arrayContaining([
              expect.objectContaining({
                benefit_amount_dollars: null,
              }),
            ]),
          }
        );
      });

      it("calls claims.update without coercing an undefined amount to null", async () => {
        expect.assertions();

        delete claim.employer_benefits[0].benefit_amount_dollars;

        ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails, {
          claimAttrs: claim,
          render: "mount",
        }));

        const { submitForm } = simulateEvents(wrapper);
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employer_benefits: expect.arrayContaining([
              expect.objectContaining({
                benefit_amount_dollars: undefined,
              }),
            ]),
          }
        );
      });
    });

    describe("when the user clicks 'Add another'", () => {
      it("adds another benefit", async () => {
        act(() => {
          wrapper.find("RepeatableFieldset").simulate("addClick");
        });

        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employer_benefits: [
              ...claim.employer_benefits,
              new EmployerBenefit(),
            ],
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

      describe("and the benefit isn't saved to the API", () => {
        it("removes the benefit", async () => {
          appLogic.claims.update.mockImplementationOnce(
            (applicationId, patchData) => {
              expect(applicationId).toBe(claim.application_id);
              expect(patchData.employer_benefits).toHaveLength(1);
            }
          );

          await act(async () => {
            await removeButton.simulate("click");
          });
          await submitForm();

          expect(
            appLogic.otherLeaves.removeEmployerBenefit
          ).not.toHaveBeenCalled();
          expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
        });
      });

      describe("and the benefit is saved to the API", () => {
        beforeEach(() => {
          claim.employer_benefits[0].employer_benefit_id =
            "mock-employer-benefit-id-1";
        });

        describe("when the DELETE request succeeds", () => {
          it("removes the benefit", async () => {
            appLogic.claims.update.mockImplementationOnce(
              (applicationId, patchData) => {
                expect(applicationId).toBe(claim.application_id);
                expect(patchData.employer_benefits).toHaveLength(1);
              }
            );

            await act(async () => {
              await removeButton.simulate("click");
            });
            await submitForm();

            expect(
              appLogic.otherLeaves.removeEmployerBenefit
            ).toHaveBeenCalled();
            expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
          });
        });

        describe("when the DELETE request fails", () => {
          beforeEach(() => {
            appLogic.otherLeaves.removeEmployerBenefit.mockImplementationOnce(
              () => false
            );
          });

          it("does not remove the benefit", async () => {
            appLogic.claims.update.mockImplementationOnce(
              (applicationId, patchData) => {
                expect(applicationId).toBe(claim.application_id);
                expect(patchData.employer_benefits).toHaveLength(2);
              }
            );

            await act(async () => {
              await removeButton.simulate("click");
            });
            await submitForm();

            expect(
              appLogic.otherLeaves.removeEmployerBenefit
            ).toHaveBeenCalled();
            expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
          });
        });
      });
    });
  });

  describe("when the user selects one of each benefit type", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(
        EmployerBenefitDetails,
        {
          claimAttrs: {
            employer_benefits: [
              new EmployerBenefit({
                benefit_type: EmployerBenefitType.paidLeave,
              }),
              new EmployerBenefit({
                benefit_type: EmployerBenefitType.shortTermDisability,
              }),
              new EmployerBenefit({
                benefit_type: EmployerBenefitType.permanentDisability,
              }),
              new EmployerBenefit({
                benefit_type: EmployerBenefitType.familyOrMedicalLeave,
              }),
            ],
          },
          render: "mount",
        }
      ));
    });
  });

  describe("when the user's claim does not have employer benefits", () => {
    beforeEach(() => {
      ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails));
    });

    it("adds a blank entry so a card is rendered", () => {
      const entries = wrapper.find(RepeatableFieldset).prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new EmployerBenefit());
    });
  });

  describe("when there are validation errors", () => {
    it.todo("updates the formState with employer_benefit_ids - see CP-1686");
  });
});

describe("EmployerBenefitCard", () => {
  let wrapper;
  const index = 0;

  beforeEach(() => {
    const entry = new EmployerBenefit();
    let getFunctionalInputProps;

    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields: jest.fn(),
      });
    });

    wrapper = shallow(
      <EmployerBenefitCard
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
      />
    );
  });

  it("renders fields for an EmployerBenefit instance", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("doesn't include Unknown as a benefit type option", () => {
    const field = wrapper.find({
      name: `employer_benefits[${index}].benefit_type`,
    });

    expect(field.prop("choices")).not.toContainEqual(
      expect.objectContaining({ value: EmployerBenefitType.unknown })
    );
  });
});
