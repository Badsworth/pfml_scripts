import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import EmployerBenefitDetails from "../../../src/pages/claims/employer-benefit-details";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefitDetails", () => {
  let appLogic, claim, wrapper;

  describe("when the user's claim has employer benefits", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(
        EmployerBenefitDetails,
        {
          claimAttrs: {
            employer_benefits: [
              new EmployerBenefit({ benefit_type: "paidLeave" }),
            ],
          },
        }
      ));
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls updateClaim", () => {
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.updateClaim).toHaveBeenCalledWith(
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
        expect(appLogic.updateClaim).toHaveBeenCalledWith(
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
        expect(appLogic.updateClaim).toHaveBeenCalledWith(
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
