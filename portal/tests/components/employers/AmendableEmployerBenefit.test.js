import EmployerBenefits, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import AmendButton from "../../../src/components/employers/AmendButton";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import InputDate from "../../../src/components/InputDate";
import InputText from "../../../src/components/InputText";
import React from "react";
import { shallow } from "enzyme";

describe("AmendableEmployerBenefit", () => {
  const shortTermDisability = new EmployerBenefits({
    benefit_amount_dollars: 1000,
    benefit_end_date: "2021-03-01",
    benefit_start_date: "2021-02-01",
    benefit_type: EmployerBenefitType.shortTermDisability,
  });
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(
      <AmendableEmployerBenefit benefit={shortTermDisability} />
    );
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders formatted date range for benefit used by employee", () => {
    expect(wrapper.find("th").last().text()).toEqual("2/1/2021 – 3/1/2021");
  });

  it("renders formatted benefit type as sentence case", () => {
    expect(wrapper.find("td").first().text()).toEqual(
      "Short-term disability insurance"
    );
  });

  it("renders an AmendmentForm if user clicks on AmendButton", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(AmendmentForm).exists()).toEqual(true);
  });

  it("renders several input fields in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(InputDate)).toHaveLength(2);
    expect(wrapper.find(InputText)).toHaveLength(1);
  });

  it("hides amount input field if the benefit is acrrued paid leave", () => {
    const paidLeave = new EmployerBenefits({
      benefit_amount_dollars: 0,
      benefit_end_date: "2021-03-01",
      benefit_start_date: "2021-02-01",
      benefit_type: EmployerBenefitType.paidLeave,
    });
    const wrapper = shallow(<AmendableEmployerBenefit benefit={paidLeave} />);

    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(InputDate)).toHaveLength(2);
    expect(wrapper.find(InputText)).toHaveLength(0);
  });
});
