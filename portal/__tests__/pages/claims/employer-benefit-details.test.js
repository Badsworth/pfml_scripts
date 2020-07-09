import { mount, shallow } from "enzyme";
import Claim from "../../../src/models/Claim";
import EmployerBenefit from "../../../src/models/EmployerBenefit";
import { EmployerBenefitDetails } from "../../../src/pages/claims/employer-benefit-details";
import QuestionPage from "../../../src/components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefitDetails", () => {
  let appLogic, claim, wrapper;
  const application_id = "12345";

  describe("when the user's claim has employer benefits", () => {
    beforeEach(() => {
      claim = new Claim({
        application_id,
        employer_benefits: [new EmployerBenefit({ benefit_type: "paidLeave" })],
      });
      testHook(() => {
        appLogic = useAppLogic();
      });
      wrapper = shallow(
        <EmployerBenefitDetails claim={claim} appLogic={appLogic} />
      );
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls updateClaim", () => {
        act(() => {
          wrapper.find(QuestionPage).simulate("save");
        });
        expect(appLogic.updateClaim).toHaveBeenCalledWith(application_id, {
          employer_benefits: claim.employer_benefits,
        });
      });
    });

    describe("when the user clicks 'Add another'", () => {
      it("adds another benefit", () => {
        act(() => {
          wrapper.find(RepeatableFieldset).simulate("addClick");
          wrapper.find(QuestionPage).simulate("save");
        });
        expect(appLogic.updateClaim).toHaveBeenCalledWith(application_id, {
          employer_benefits: [
            ...claim.employer_benefits,
            new EmployerBenefit(),
          ],
        });
      });
    });

    describe("when the user clicks 'Remove'", () => {
      it("removes the benefit", () => {
        act(() => {
          wrapper
            .find(RepeatableFieldset)
            .dive()
            .find(RepeatableFieldsetCard)
            .simulate("removeClick");
          wrapper.find(QuestionPage).simulate("save");
        });
        expect(appLogic.updateClaim).toHaveBeenCalledWith(application_id, {
          employer_benefits: [],
        });
      });
    });
  });

  describe("when the user selects one of each benefit type", () => {
    beforeEach(() => {
      claim = new Claim({
        application_id,
        employer_benefits: [
          new EmployerBenefit({ benefit_type: "paidLeave" }),
          new EmployerBenefit({ benefit_type: "shortTermDisability" }),
          new EmployerBenefit({ benefit_type: "permanentDisability" }),
          new EmployerBenefit({ benefit_type: "familyOrMedicalLeave" }),
        ],
      });
      wrapper = mount(<EmployerBenefitDetails claim={claim} appLogic={{}} />);
    });

    it("only renders the amount input text component for insurance benefit types", () => {
      expect(
        wrapper.find('InputText[name="employer_benefits[0].benefit_amount"]')
      ).toHaveLength(0);
      expect(
        wrapper.find('InputText[name="employer_benefits[1].benefit_amount"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('InputText[name="employer_benefits[2].benefit_amount"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('InputText[name="employer_benefits[3].benefit_amount"]')
      ).toHaveLength(1);
    });
  });

  describe("when the user's claim does not have employer benefits", () => {
    beforeEach(() => {
      claim = new Claim({
        application_id,
      });
      testHook(() => {
        appLogic = useAppLogic();
      });
      wrapper = shallow(
        <EmployerBenefitDetails claim={claim} appLogic={appLogic} />
      );
    });

    describe("when user clicks continue", () => {
      it("creates and saves a blank employer benefit object", () => {
        act(() => {
          wrapper.find(QuestionPage).simulate("save");
        });
        expect(appLogic.updateClaim).toHaveBeenCalledWith(application_id, {
          employer_benefits: [new EmployerBenefit()],
        });
      });
    });
  });
});
