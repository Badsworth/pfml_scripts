/* eslint-disable react/jsx-key */
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import EmployerBenefits from "../../../src/components/employers/EmployerBenefits";
import React from "react";
import { shallow } from "enzyme";

describe("EmployerBenefits", () => {
  it("renders the component", () => {
    const benefits = new EmployerBenefit({
      benefit_amount_dollars: 1000,
      benefit_end_date: "2021-03-01",
      benefit_start_date: "2021-02-01",
      benefit_type: EmployerBenefitType.shortTermDisability,
    });
    const wrapper = shallow(
      <EmployerBenefits employerBenefits={[benefits]} onChange={() => {}} />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' if no benefits are reported", () => {
    const wrapper = shallow(
      <EmployerBenefits employerBenefits={[]} onChange={() => {}} />
    );

    expect(wrapper.find(AmendableEmployerBenefit).exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });
});
