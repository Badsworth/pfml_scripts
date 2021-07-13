import { createInputElement, testHook } from "../test-utils";
import { mount, shallow } from "enzyme";
import InputHours from "../../src/components/InputHours";
import React from "react";
import useHandleInputChange from "../../src/hooks/useHandleInputChange";

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
        .find("InputNumber")
        .props()
        .formGroupClassName.includes("margin-top-105")
    ).toBe(true);
    expect(
      wrapper
        .find("Dropdown")
        .props()
        .formGroupClassName.includes("margin-top-105")
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
        .find("InputNumber")
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

    expect(wrapper.find("InputNumber").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(15);
  });

  it("renders correctly with 0 minutes", () => {
    const { wrapper } = render({ value: 60 });
    expect(wrapper.find("InputNumber").props().value).toEqual(1);
    expect(wrapper.find("Dropdown").props().value).toEqual(0);
  });

  it("renders correctly if both hours and minutes are 0", () => {
    const { wrapper } = render({ value: 0 });
    expect(wrapper.find("InputNumber").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(0);
  });

  it("renders empty hours and minutes if value is undefined", () => {
    const { wrapper } = render({ value: undefined });
    expect(wrapper.find("InputNumber").props().value).toEqual("");
    expect(wrapper.find("Dropdown").props().value).toEqual("");
  });

  it("logs warning if minutesIncrements is not a multiple of value", () => {
    const warnSpy = jest
      .spyOn(console, "warn")
      .mockImplementationOnce(() => {});

    const { wrapper } = render({ value: 33, minutesIncrement: 15 });
    expect(wrapper.find("InputNumber").props().value).toEqual(0);
    expect(wrapper.find("Dropdown").props().value).toEqual(33);
    expect(warnSpy).toHaveBeenCalled();
  });

  it("renders empty hours if hours value is erased and minutes value is 0", () => {
    const { wrapper, props } = render({ value: 8 * 60 });

    wrapper.find("InputNumber").simulate("change", {
      target: createInputElement({ value: "" }),
    });

    expect(props.onChange.mock.calls[0][0].target.value).toBe("");
  });

  it("sets hours to 0 if hours are erased and minutes are greater than 0", () => {
    const { wrapper, props } = render({ value: 8 * 60 + 15 });

    wrapper.find("InputNumber").simulate("change", {
      target: createInputElement({ value: "" }),
    });

    expect(props.onChange.mock.calls[0][0].target.value).toBe("15");
  });

  it("renders empty hours if minutes value is erased and hours value is 0", () => {
    const { wrapper, props } = render({ value: 15 });

    wrapper.find("Dropdown").simulate("change", {
      target: createInputElement({ value: "" }),
    });

    expect(props.onChange.mock.calls[0][0].target.value).toBe("");
  });

  it("sets minutes to 0 if minutes are erased and hours are greater than 0", () => {
    const { wrapper, props } = render({ value: 8 * 60 + 15 });

    wrapper.find("Dropdown").simulate("change", {
      target: createInputElement({ value: "" }),
    });

    expect(props.onChange.mock.calls[0][0].target.value).toBe("480");
  });

  it("propagates valid input with useHandleInputChange", () => {
    const updateFields = jest.fn();
    let onChange;
    testHook(() => {
      onChange = useHandleInputChange(updateFields);
    });

    const { wrapper } = render(
      {
        name: "minutes",
        onChange,
      },
      true
    );

    const input = wrapper.find("input");

    input.simulate("change", {
      // create input element with all the necessary attributes for parsing the value
      target: createInputElement({ ...input.props(), value: "1" }),
    });

    expect(updateFields).toHaveBeenCalledTimes(1);
    expect(updateFields).toHaveBeenCalledWith(
      expect.objectContaining({
        minutes: 60,
      })
    );
  });

  it("does not propagate invalid input with useHandleInputChange", () => {
    const updateFields = jest.fn();
    let onChange;
    testHook(() => {
      onChange = useHandleInputChange(updateFields);
    });

    const { wrapper } = render(
      {
        name: "minutes",
        onChange,
      },
      true
    );

    const input = wrapper.find("input");

    input.simulate("change", {
      // create input element with all the necessary attributes for parsing the value
      target: createInputElement({ ...input.props(), value: "-1" }),
    });

    expect(updateFields).not.toHaveBeenCalled();
  });
});
