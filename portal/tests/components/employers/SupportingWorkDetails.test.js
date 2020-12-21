import AmendButton from "../../../src/components/employers/AmendButton";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import Button from "../../../src/components/Button";
import InputText from "../../../src/components/InputText";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import SupportingWorkDetails from "../../../src/components/employers/SupportingWorkDetails";
import { shallow } from "enzyme";

describe("SupportingWorkDetails", () => {
  const hoursWorkedPerWeek = 30;
  const props = {
    onChange: jest.fn(),
    hoursWorkedPerWeek,
  };
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<SupportingWorkDetails {...props} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("has a ReviewRow that takes in an AmendButton", () => {
    expect(
      wrapper.find(ReviewRow).first().render().find(".amend-text").text()
    ).toEqual("Amend");
  });

  it("renders weekly hours", () => {
    expect(wrapper.find("p").first().text()).toEqual(
      hoursWorkedPerWeek.toString()
    );
  });

  it("renders amended value on change", () => {
    wrapper.find(ReviewRow).first().dive(3).find(AmendButton).simulate("click");
    wrapper.find(InputText).simulate("change", { target: { value: "10" } });

    expect(props.onChange).toHaveBeenCalled();
  });

  it("hides amendment form and clears value on cancel", () => {
    wrapper.find(ReviewRow).first().dive(3).find(AmendButton).simulate("click");
    wrapper.find(InputText).simulate("change", { target: { value: "10" } });
    wrapper.find(AmendmentForm).dive().find(Button).simulate("click");

    expect(props.onChange).toHaveBeenCalledTimes(2);
  });

  it("formats empty, zero, invalid amount values to 0", () => {
    wrapper.find(ReviewRow).first().dive(3).find(AmendButton).simulate("click");
    wrapper.find(InputText).simulate("change", { target: { value: "" } });
    expect(props.onChange).toHaveBeenCalledWith(0);

    wrapper.find(InputText).simulate("change", { target: { value: "0" } });
    expect(props.onChange).toHaveBeenCalledWith(0);

    wrapper.find(InputText).simulate("change", { target: { value: "hello" } });
    expect(props.onChange).toHaveBeenCalledWith(0);
  });

  it("formats decimal amount values", () => {
    wrapper.find(ReviewRow).first().dive(3).find(AmendButton).simulate("click");
    wrapper
      .find(InputText)
      .simulate("change", { target: { value: "100.5000" } });

    expect(props.onChange).toHaveBeenCalledWith(100.5);
  });

  it("formats amount values without commas", () => {
    wrapper.find(ReviewRow).first().dive(3).find(AmendButton).simulate("click");
    wrapper.find(InputText).simulate("change", { target: { value: "1000" } });

    expect(props.onChange).toHaveBeenCalledWith(1000);
  });
});
