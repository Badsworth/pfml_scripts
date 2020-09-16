/* eslint-disable react/jsx-key */
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import EmployerBenefits from "../../../src/components/employers/EmployerBenefits";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("EmployerBenefits", () => {
  it("renders the component", () => {
    const wrapper = shallow(
      <EmployerBenefits benefits={claim.employer_benefits} />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' if no benefits are reported", () => {
    const wrapper = shallow(<EmployerBenefits benefits={[]} />);

    expect(wrapper.find(AmendableEmployerBenefit).exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });
});
