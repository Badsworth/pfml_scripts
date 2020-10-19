import { mount, shallow } from "enzyme";
import InputHours from "../../src/components/InputHours";
import React from "react";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      label: "Label",
      hoursLabel: "Hours Label",
      minutesLabel: "Minutes Label",
      name: "field-name",
      minutesIncrement: 15,
      emptyMinutesLabel: "Select minute",
      onChange: jest.fn(),
    },
    customProps
  );

  const component = <InputHours {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("InputHours", () => {
  it("renders component", () => {
    const { wrapper } = render({ value: 40 * 60 + 15 });

    expect(wrapper).toMatchSnapshot();
  });

  it("tightens label spacing if smallLabel prop is true", () => {
    const { wrapper } = render({ smallLabel: true });

    expect(
      wrapper
        .find("InputText")
        .props()
        .formGroupClassName.includes("margin-top-neg-105")
    ).toBe(true);
    expect(
      wrapper
        .find("Dropdown")
        .props()
        .formGroupClassName.includes("margin-top-neg-105")
    ).toBe(true);
  });

  it("passes errorMsg to FormLabel if errorMsg is set", () => {
    const { wrapper } = render({ errorMsg: "Something went wrong" });

    expect(wrapper.find("FormLabel").props().errorMsg).toEqual(
      "Something went wrong"
    );
    expect(wrapper.find("Fieldset").hasClass("usa-form-group--error")).toBe(
      true
    );
  });

  it("adds error class to the day input component when hoursInvalid is true", () => {
    const { wrapper } = render({ hoursInvalid: true });

    expect(
      wrapper
        .find("InputText")
        .props()
        .inputClassName.includes("usa-input--error")
    ).toBe(true);
  });

  it("adds error class to the month input component when minutesInvalid is true", () => {
    const { wrapper } = render({ minutesInvalid: true });

    expect(
      wrapper
        .find("Dropdown")
        .props()
        .selectClassName.includes("usa-input--error")
    ).toBe(true);
  });

  it("renders correctly if there are 0 hours", () => {
    const { wrapper } = render({ value: 15 });

    expect(wrapper.find("InputText").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(15);
  });

  it("renders correctly with 0 minutes", () => {
    const { wrapper } = render({ value: 60 });
    expect(wrapper.find("InputText").props().value).toEqual(1);
    expect(wrapper.find("Dropdown").props().value).toEqual(0);
  });

  it("renders correctly if both hours and minutes are 0", () => {
    const { wrapper } = render({ value: 0 });
    expect(wrapper.find("InputText").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(0);
  });

  it("renders 0 hours and 0 minutes if value is null", () => {
    const { wrapper } = render({ value: null });
    expect(wrapper.find("InputText").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(0);
  });

  it("logs warning if minutesIncrements is not a multiple of value", () => {
    const warnSpy = jest
      .spyOn(console, "warn")
      .mockImplementationOnce(() => {});

    const { wrapper } = render({ value: 33, minutesIncrement: 15 });
    expect(wrapper.find("InputText").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(33);
    expect(warnSpy).toHaveBeenCalled();
  });
});
