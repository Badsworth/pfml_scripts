import EmployerBenefit, {
  EmployerBenefitType,
  IncomeFrequency,
} from "../../../src/models/EmployerBenefit";
import AmendButton from "../../../src/components/employers/AmendButton";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import Button from "../../../src/components/Button";
import Dropdown from "../../../src/components/Dropdown";
import InputDate from "../../../src/components/InputDate";
import InputText from "../../../src/components/InputText";
import React from "react";
import { shallow } from "enzyme";

describe("AmendableEmployerBenefit", () => {
  const shortTermDisability = new EmployerBenefit({
    benefit_amount_dollars: 1000,
    benefit_amount_frequency: IncomeFrequency.monthly,
    benefit_end_date: "2021-03-01",
    benefit_start_date: "2021-02-01",
    benefit_type: EmployerBenefitType.shortTermDisability,
  });
  const props = {
    onChange: jest.fn(),
    benefit: shortTermDisability,
  };
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<AmendableEmployerBenefit {...props} />);
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

  it("renders formatted benefit amount with dollar sign", () => {
    expect(wrapper.find("td").at(1).text()).toEqual("$1,000.00 per month");
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

  it("renders amount field with currency mask", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(InputText).prop("mask")).toEqual("currency");
  });

  it("hides amount input field if the benefit is acrrued paid leave", () => {
    const paidLeave = new EmployerBenefit({
      benefit_amount_dollars: 0,
      benefit_amount_frequency: "",
      benefit_end_date: "2021-03-01",
      benefit_start_date: "2021-02-01",
      benefit_type: EmployerBenefitType.paidLeave,
    });
    const wrapper = shallow(
      <AmendableEmployerBenefit benefit={paidLeave} onChange={() => {}} />
    );

    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(InputDate)).toHaveLength(2);
    expect(wrapper.find(InputText)).toHaveLength(0);
  });

  it("updates start and end dates in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper
      .find(InputDate)
      .first()
      .simulate("change", { target: { value: "2020-10-10" } });
    wrapper
      .find(InputDate)
      .last()
      .simulate("change", { target: { value: "2020-10-20" } });

    expect(props.onChange).toHaveBeenCalledTimes(2);
    expect(wrapper.find(InputDate).first().prop("value")).toEqual("2020-10-10");
    expect(wrapper.find(InputDate).last().prop("value")).toEqual("2020-10-20");
  });

  it("updates amount in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(InputText).simulate("change", { target: { value: 500 } });

    expect(props.onChange).toHaveBeenCalled();
    expect(wrapper.find(InputText).prop("value")).toEqual(500);
  });

  it("updates frequency in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper
      .find(Dropdown)
      .simulate("change", { target: { value: IncomeFrequency.weekly } });

    expect(props.onChange).toHaveBeenCalled();
    expect(wrapper.find(Dropdown).prop("value")).toEqual(
      IncomeFrequency.weekly
    );
  });

  it("restores original value on cancel", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(InputText).simulate("change", { target: { value: 500 } });

    expect(wrapper.find(InputText).prop("value")).toEqual(500);

    wrapper.find(AmendmentForm).dive().find(Button).simulate("click");

    wrapper.find(AmendButton).simulate("click");
    expect(wrapper.find(InputText).prop("value")).toEqual(1000);
  });
});
