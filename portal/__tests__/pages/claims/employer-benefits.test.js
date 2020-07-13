import Claim from "../../../src/models/Claim";
import { EmployerBenefits } from "../../../src/pages/claims/employer-benefits";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefits", () => {
  let appLogic, claim, wrapper;
  const application_id = "12345";

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    claim = new Claim({ application_id });
    wrapper = shallow(<EmployerBenefits claim={claim} appLogic={appLogic} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks continue", () => {
    it("calls updateClaim", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      expect(appLogic.updateClaim).toHaveBeenCalledWith(application_id, {
        has_employer_benefits: claim.has_employer_benefits,
      });
    });
  });
});
