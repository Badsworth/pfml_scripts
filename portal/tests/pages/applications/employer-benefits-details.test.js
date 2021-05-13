import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import EmployerBenefitsDetails, {
  EmployerBenefitCard,
} from "../../../src/pages/applications/employer-benefits-details";
import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs) => {
  const claim = new MockBenefitsApplicationBuilder().continuous().create();

  const { appLogic, wrapper } = renderWithAppLogic(EmployerBenefitsDetails, {
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

const benefitData = {
  benefit_type: EmployerBenefitType.shortTermDisability,
  benefit_start_date: "2021-03-01",
  benefit_end_date: "2021-04-01",
  benefit_amount_dollars: 100,
  benefit_amount_frequency: EmployerBenefitFrequency.monthly,
  employer_benefit_id: null,
};

const setBenefitFields = (wrapper, benefit) => {
  const employerBenefitCard = wrapper
    .find(RepeatableFieldset)
    .dive()
    .find(RepeatableFieldsetCard)
    .first()
    .dive()
    .find("EmployerBenefitCard")
    .first()
    .dive();

  const { changeRadioGroup, changeField } = simulateEvents(employerBenefitCard);
  changeRadioGroup("employer_benefits[0].benefit_type", benefit.benefit_type);
  changeField(
    "employer_benefits[0].benefit_start_date",
    benefit.benefit_start_date
  );
  changeField(
    "employer_benefits[0].benefit_end_date",
    benefit.benefit_end_date
  );
  changeField(
    "employer_benefits[0].benefit_amount_dollars",
    benefit.benefit_amount_dollars
  );
  changeField(
    "employer_benefits[0].benefit_amount_frequency",
    benefit.benefit_amount_frequency
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

const clickAddBenefitButton = async (wrapper) => {
  await wrapper
    .find(RepeatableFieldset)
    .dive()
    .find({ name: "add-entry-button" })
    .simulate("click");
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

describe("EmployerBenefitsDetails", () => {
  describe("when the user's claim has no employer benefits", () => {
    it("renders the page", () => {
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
    });

    it("adds a blank entry so a card is rendered", () => {
      const { wrapper } = setup();
      const entries = wrapper.find(RepeatableFieldset).prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new EmployerBenefit());

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
          .length
      ).toEqual(1);
    });

    it("calls claims.update with new benefits data when user clicks continue", async () => {
      const { appLogic, claim, submitForm, wrapper } = setup();

      setBenefitFields(wrapper, benefitData);

      const entries = wrapper.find(RepeatableFieldset).prop("entries");
      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(benefitData);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          employer_benefits: [benefitData],
        }
      );
    });

    it("adds an empty benefit when the user clicks Add Another Benefit", async () => {
      const { wrapper } = setup();

      setBenefitFields(wrapper, benefitData);
      await clickAddBenefitButton(wrapper);

      const entries = wrapper.find(RepeatableFieldset).prop("entries");
      expect(entries).toHaveLength(2);
      expect(entries).toEqual([benefitData, new EmployerBenefit()]);

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
      ).toHaveLength(2);
    });

    it("removes a benefit when the user clicks Remove Benefit", async () => {
      const { wrapper } = setup();

      setBenefitFields(wrapper, benefitData);

      await clickAddBenefitButton(wrapper);

      await clickFirstRemoveButton(wrapper);

      const entries = wrapper.find(RepeatableFieldset).prop("entries");
      expect(entries).toHaveLength(1);
      expect(entries).toEqual([new EmployerBenefit()]);

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
      ).toHaveLength(1);
    });
  });

  describe("when the user's claim has employer benefits", () => {
    it("renders the page", () => {
      const claimWithBenefits = createClaimWithBenefits();
      const { wrapper } = setup(claimWithBenefits);
      expect(wrapper).toMatchSnapshot();
    });

    it("adds another benefit when the user clicks 'Add another'", async () => {
      const claimWithBenefits = createClaimWithBenefits();
      const { appLogic, claim, submitForm, wrapper } = setup(claimWithBenefits);

      clickAddBenefitButton(wrapper);

      expect(
        wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
          .length
      ).toEqual(3);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          employer_benefits: [
            ...claimWithBenefits.employer_benefits,
            new EmployerBenefit(),
          ],
        }
      );
    });

    it("calls claims.update when user clicks continue", async () => {
      const claimWithBenefits = createClaimWithBenefits();
      const { appLogic, claim, submitForm } = setup(claimWithBenefits);
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          employer_benefits: claimWithBenefits.employer_benefits,
        }
      );
    });

    describe("when the user clicks 'Remove'", () => {
      it("removes the benefit when the benefit isn't saved to the API", async () => {
        const claimWithBenefits = createClaimWithBenefits();
        const { appLogic, submitForm, wrapper } = setup(claimWithBenefits);
        appLogic.benefitsApplications.update.mockImplementationOnce(
          (applicationId, patchData) => {
            expect(applicationId).toBe(claimWithBenefits.application_id);
            expect(patchData.employer_benefits).toHaveLength(1);
          }
        );

        await clickFirstRemoveButton(wrapper);
        await submitForm();

        expect(
          appLogic.otherLeaves.removeEmployerBenefit
        ).not.toHaveBeenCalled();

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);
      });

      it("removes the benefit when the benefit is saved to the API and the DELETE request succeeds", async () => {
        const claimWithBenefits = createClaimWithBenefits();
        claimWithBenefits.employer_benefits[0].employer_benefit_id =
          "mock-employer-benefit-id-1";

        const { appLogic, submitForm, wrapper } = setup(claimWithBenefits);

        appLogic.benefitsApplications.update.mockImplementationOnce(
          (applicationId, patchData) => {
            expect(applicationId).toBe(claimWithBenefits.application_id);
            expect(patchData.employer_benefits).toHaveLength(1);
          }
        );

        await clickFirstRemoveButton(wrapper);
        await submitForm();

        const entries = wrapper.find(RepeatableFieldset).prop("entries");

        expect(appLogic.otherLeaves.removeEmployerBenefit).toHaveBeenCalled();
        expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);
        expect(entries).toHaveLength(1);
        expect(
          wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
        ).toHaveLength(1);
      });

      it("does not remove the benefit when the benefit is saved to the API and the DELETE request fails", async () => {
        const claimWithBenefits = createClaimWithBenefits();
        claimWithBenefits.employer_benefits[0].employer_benefit_id =
          "mock-employer-benefit-id-1";

        const { appLogic, submitForm, wrapper } = setup(claimWithBenefits);

        appLogic.otherLeaves.removeEmployerBenefit.mockImplementationOnce(
          () => false
        );

        appLogic.benefitsApplications.update.mockImplementationOnce(
          (applicationId, patchData) => {
            expect(applicationId).toBe(claimWithBenefits.application_id);
            expect(patchData.employer_benefits).toHaveLength(2);
          }
        );

        await clickFirstRemoveButton(wrapper);
        expect(appLogic.otherLeaves.removeEmployerBenefit).toHaveBeenCalled();

        await submitForm();
        expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);

        const entries = wrapper.find(RepeatableFieldset).prop("entries");
        expect(entries).toHaveLength(2);
        expect(
          wrapper.find(RepeatableFieldset).dive().find(RepeatableFieldsetCard)
        ).toHaveLength(2);
      });
    });
  });

  describe("when there are validation errors", () => {
    it.todo("updates the formState with employer_benefit_ids - see CP-1686");
  });
});

const setupBenefitCard = () => {
  const index = 0;
  const entry = new EmployerBenefit();
  let getFunctionalInputProps;

  testHook(() => {
    getFunctionalInputProps = useFunctionalInputProps({
      appErrors: new AppErrorInfoCollection(),
      formState: {},
      updateFields: jest.fn(),
    });
  });

  const wrapper = shallow(
    <EmployerBenefitCard
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

describe("EmployerBenefitCard", () => {
  it("renders fields for an EmployerBenefit instance", () => {
    const { wrapper } = setupBenefitCard();
    expect(wrapper).toMatchSnapshot();
  });

  it("doesn't include Unknown as a benefit type option", () => {
    const { index, wrapper } = setupBenefitCard();
    const field = wrapper.find({
      name: `employer_benefits[${index}].benefit_type`,
    });

    expect(field.prop("choices")).not.toContainEqual(
      expect.objectContaining({ value: EmployerBenefitType.unknown })
    );
  });
});
