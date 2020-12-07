import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import EmployerBenefitDetails, {
  EmployerBenefitCard,
} from "../../../src/pages/applications/employer-benefit-details";
import {
  MockClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefitDetails", () => {
  let appLogic, claim, wrapper;

  describe("when the user's claim has employer benefits", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().continuous().employerBenefit().create();

      ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails, {
        claimAttrs: claim,
      }));
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls claims.update", () => {
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employer_benefits: claim.employer_benefits,
          }
        );
      });
    });

    describe("when the user clicks 'Add another'", () => {
      it("adds another benefit", () => {
        act(() => {
          wrapper.find("RepeatableFieldset").simulate("addClick");
          wrapper.find("QuestionPage").simulate("save");
        });
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
      it("removes the benefit", () => {
        act(() => {
          wrapper
            .find("RepeatableFieldset")
            .dive()
            .find("RepeatableFieldsetCard")
            .simulate("removeClick");
          wrapper.find("QuestionPage").simulate("save");
        });
        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employer_benefits: [],
          }
        );
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

    it("only renders the amount input text component for insurance benefit types", () => {
      expect(
        wrapper.find(
          'InputText[name="employer_benefits[0].benefit_amount_dollars"]'
        )
      ).toHaveLength(0);
      expect(
        wrapper.find(
          'InputText[name="employer_benefits[1].benefit_amount_dollars"]'
        )
      ).toHaveLength(1);
      expect(
        wrapper.find(
          'InputText[name="employer_benefits[2].benefit_amount_dollars"]'
        )
      ).toHaveLength(1);
      expect(
        wrapper.find(
          'InputText[name="employer_benefits[3].benefit_amount_dollars"]'
        )
      ).toHaveLength(1);
    });
  });

  describe("when the user's claim does not have employer benefits", () => {
    beforeEach(() => {
      ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefitDetails));
    });

    it("adds a blank entry so a card is rendered", () => {
      const entries = wrapper.find("RepeatableFieldset").prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new EmployerBenefit());
    });
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
