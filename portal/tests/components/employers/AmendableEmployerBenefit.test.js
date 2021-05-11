import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import AmendButton from "../../../src/components/employers/AmendButton";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import Button from "../../../src/components/Button";
import Dropdown from "../../../src/components/Dropdown";
import InputDate from "../../../src/components/InputDate";
import InputNumber from "../../../src/components/InputNumber";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

describe("AmendableEmployerBenefit", () => {
  const shortTermDisability = new EmployerBenefit({
    benefit_amount_dollars: 1000,
    benefit_amount_frequency: EmployerBenefitFrequency.monthly,
    benefit_end_date: "2021-03-01",
    benefit_start_date: "2021-02-01",
    benefit_type: EmployerBenefitType.shortTermDisability,
    employer_benefit_id: 0,
  });
  const onChange = jest.fn();
  const employerBenefit = shortTermDisability;

  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(
      <AmendableEmployerBenefit
        appErrors={appLogic.appErrors}
        employerBenefit={employerBenefit}
        onChange={onChange}
      />
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

  it("renders formatted benefit amount with dollar sign and frequency", () => {
    expect(wrapper.find("td").at(1).text()).toEqual("$1,000.00 per month");
  });

  it("renders information about unknown frequency when frequency is 'Unknown'", () => {
    const paidLeave = new EmployerBenefit({
      benefit_amount_dollars: 0,
      benefit_amount_frequency: "Unknown",
      benefit_end_date: "2021-03-01",
      benefit_start_date: "2021-02-01",
      benefit_type: EmployerBenefitType.paidLeave,
      employer_benefit_id: 0,
    });
    const wrapper = shallow(
      <AmendableEmployerBenefit
        appErrors={appLogic.appErrors}
        employerBenefit={paidLeave}
        onChange={() => {}}
      />
    );

    expect(wrapper.find("td").at(1).text()).toEqual(
      "$0.00 (frequency unknown)"
    );
  });

  it("renders an AmendmentForm if user clicks on AmendButton", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(AmendmentForm).exists()).toEqual(true);
  });

  it("renders several input fields in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(InputDate)).toHaveLength(2);
    expect(wrapper.find(InputNumber)).toHaveLength(1);
  });

  it("renders amount field with currency mask", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(InputNumber).prop("mask")).toEqual("currency");
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

    expect(onChange).toHaveBeenCalledTimes(2);
    expect(wrapper.find(InputDate).first().prop("value")).toEqual("2020-10-10");
    expect(wrapper.find(InputDate).last().prop("value")).toEqual("2020-10-20");
  });

  it("updates amount in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(InputNumber).simulate("change", { target: { value: "500" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 500 })
    );
    expect(wrapper.find(InputNumber).prop("value")).toEqual("500");
  });

  it("formats empty, zero, invalid amount values to 0", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(InputNumber).simulate("change", { target: { value: "" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 0 })
    );
    expect(wrapper.find(InputNumber).prop("value")).toEqual(0);

    wrapper.find(InputNumber).simulate("change", { target: { value: "0" } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 0 })
    );
    expect(wrapper.find(InputNumber).prop("value")).toEqual(0);

    wrapper
      .find(InputNumber)
      .simulate("change", { target: { value: "hello" } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 0 })
    );
    expect(wrapper.find(InputNumber).prop("value")).toEqual(0);
  });

  it("formats decimal amount values", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper
      .find(InputNumber)
      .simulate("change", { target: { value: "100.5000" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 100.5 })
    );
  });

  it("formats amount values without commas", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(InputNumber).simulate("change", { target: { value: "1000" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 1000 })
    );
  });

  it("updates frequency in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(Dropdown).simulate("change", {
      target: { value: EmployerBenefitFrequency.weekly },
    });

    expect(onChange).toHaveBeenCalled();
    expect(wrapper.find(Dropdown).prop("value")).toEqual(
      EmployerBenefitFrequency.weekly
    );
  });

  it("restores original value on cancel", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper.find(InputNumber).simulate("change", { target: { value: "500" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ benefit_amount_dollars: 500 })
    );
    expect(wrapper.find(InputNumber).prop("value")).toEqual("500");

    wrapper.find(AmendmentForm).dive().find(Button).simulate("click");

    wrapper.find(AmendButton).simulate("click");
    expect(wrapper.find(InputNumber).prop("value")).toEqual(1000);
  });
});
