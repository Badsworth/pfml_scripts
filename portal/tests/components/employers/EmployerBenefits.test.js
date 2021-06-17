/* eslint-disable react/jsx-key */
import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import EmployerBenefits from "../../../src/components/employers/EmployerBenefits";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

const BENEFITS = [
  new EmployerBenefit({
    benefit_amount_dollars: 1000,
    benefit_amount_frequency: EmployerBenefitFrequency.weekly,
    benefit_end_date: "2021-03-01",
    benefit_start_date: "2021-02-01",
    benefit_type: EmployerBenefitType.shortTermDisability,
    employer_benefit_id: 0,
    is_full_salary_continuous: false,
  }),
  new EmployerBenefit({
    benefit_amount_dollars: 2000,
    benefit_amount_frequency: EmployerBenefitFrequency.weekly,
    benefit_end_date: "2021-05-11",
    benefit_start_date: "2021-05-01",
    benefit_type: EmployerBenefitType.paidLeave,
    employer_benefit_id: 1,
    is_full_salary_continuous: true,
  }),
];

describe("EmployerBenefits", () => {
  let appLogic;

  function render(providedProps) {
    const defaultProps = {
      addedBenefits: [],
      appErrors: appLogic.appErrors,
      employerBenefits: BENEFITS,
      onAdd: () => {},
      onChange: () => {},
      onRemove: () => {},
      shouldShowV2: false,
    };
    const componentProps = {
      ...defaultProps,
      ...providedProps,
    };
    return shallow(<EmployerBenefits {...componentProps} />);
  }

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' if no benefits are reported", () => {
    const wrapper = render({ employerBenefits: [] });
    expect(wrapper.find(AmendableEmployerBenefit).exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });

  it('displays a row for each benefit in "employerBenefits"', () => {
    const wrapper = render();

    expect(wrapper.find("AmendableEmployerBenefit").length).toBe(2);
  });

  describe("when 'shouldShowV2' is true", () => {
    it("displays rows for added benefits", () => {
      const wrapper = render({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: true,
      });

      expect(wrapper.find("AmendableEmployerBenefit").length).toBe(2);
    });

    it("displays the 'Add benefit' button", () => {
      const wrapper = render({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: true,
      });

      expect(wrapper.find("AddButton").exists()).toBe(true);
    });
  });

  describe("when 'shouldShowV2' is false", () => {
    it("does not display rows for added benefits", () => {
      const wrapper = render({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: false,
      });

      expect(wrapper.find("AmendableEmployerBenefit").length).toBe(0);
    });

    it("does not display the 'Add benefit' button", () => {
      const wrapper = render({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: false,
      });

      expect(wrapper.find("AddButton").exists()).toBe(false);
    });
  });
});
