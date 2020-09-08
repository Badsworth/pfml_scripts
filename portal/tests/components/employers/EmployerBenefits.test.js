/* eslint-disable react/jsx-key */
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import EmployerBenefits from "../../../src/components/employers/EmployerBenefits";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("EmployerBenefits", () => {
  const detailedEmployerBenefit = [
    new EmployerBenefit({
      benefit_amount_dollars: 1000,
      benefit_end_date: "2021-03-01",
      benefit_start_date: "2021-02-01",
      benefit_type: EmployerBenefitType.shortTermDisability,
    }),
  ];

  const emptyEmployerBenefit = [
    new EmployerBenefit({
      benefit_type: EmployerBenefitType.familyOrMedicalLeave,
    }),
  ];

  it("renders the component", () => {
    const wrapper = shallow(
      <EmployerBenefits employerBenefits={claim.employer_benefits} />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("renders formatted date range for benefit used by employee", () => {
    const wrapper = shallow(
      <EmployerBenefits employerBenefits={detailedEmployerBenefit} />
    );

    expect(wrapper.find("th").last().text()).toEqual("2/1/2021 – 3/1/2021");
  });

  it("renders 'N/A' for benefit not used by employee", () => {
    const wrapper = shallow(
      <EmployerBenefits employerBenefits={emptyEmployerBenefit} />
    );

    expect(wrapper.find("th").last().text()).toEqual("N/A");
  });

  it("renders formatted benefit type as sentence case", () => {
    const wrapper = shallow(
      <EmployerBenefits employerBenefits={emptyEmployerBenefit} />
    );

    expect(wrapper.find("td").first().text()).toEqual(
      "Family or medical leave insurance"
    );
  });
});
