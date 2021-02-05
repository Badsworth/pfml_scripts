import InputDate, {
  formatFieldsAsISO8601,
  parseDateParts,
} from "../../src/components/InputDate";
import { mount, shallow } from "enzyme";
import React from "react";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      label: "Field Label",
      dayLabel: "Day",
      monthLabel: "Month",
      name: "field-name",
      onChange: jest.fn(),
      yearLabel: "Year",
    },
    customProps
  );

  const component = <InputDate {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("InputDate", () => {
  it("renders separate fields for month / day / year", () => {
    const { wrapper } = render({
      name: "test-date-field",
      dayLabel: "Test Day",
      monthLabel: "Test Month",
      yearLabel: "Test Year",
    });
    const fields = wrapper.find("InputText");

    expect(fields).toMatchSnapshot();
  });

  it("renders everything within a Fieldset", () => {
    const { wrapper } = render();

    expect(wrapper.is("Fieldset")).toBe(true);
  });

  it("renders a legend for the fieldset", () => {
    const { wrapper } = render({
      label: "Legend text",
      hint: "Legend hint",
      example: "Legend example",
      optionalText: "Optional",
    });

    const legend = wrapper.find("FormLabel");

    expect(legend).toMatchSnapshot();
  });

  it("breaks apart the full date value to set the month/day/year field values", () => {
    const { wrapper } = render({
      value: "2020-10-04",
    });
    const fields = wrapper.find("InputText");

    // Month
    expect(fields.at(0).prop("value")).toBe("10");
    // Day
    expect(fields.at(1).prop("value")).toBe("04");
    // Year
    expect(fields.at(2).prop("value")).toBe("2020");
  });

  describe("when a month or day field is blurred", () => {
    it("adds a leading zero to month and day and calls the onChange prop", () => {
      // We need to mount the component so the input values can be accessed
      const mountComponent = true;
      const { props, wrapper } = render(
        {
          name: "full-date-field",
          onChange: jest.fn(),
          value: "2020--",
        },
        mountComponent
      );
      const monthInput = wrapper.find("input").at(0);
      const dayInput = wrapper.find("input").at(1);

      monthInput.getDOMNode().value = "1";
      dayInput.getDOMNode().value = "2";
      monthInput.simulate("blur");

      expect(props.onChange).toHaveBeenCalledTimes(1);
      // Read the event passed into the onChange function
      expect(props.onChange.mock.calls[0][0].target.value).toBe("2020-01-02");
    });
  });

  describe("when change event is triggered", () => {
    it("does not add a leading zero to month or days", () => {
      // We need to mount the component so the input values can be accessed
      const mountComponent = true;
      const { props, wrapper } = render(
        {
          name: "full-date-field",
          onChange: jest.fn(),
          value: "2020-07-04",
        },
        mountComponent
      );
      const monthInput = wrapper.find("input").at(0);
      const dayInput = wrapper.find("input").at(1);

      monthInput.getDOMNode().value = "1";
      dayInput.getDOMNode().value = "2";
      monthInput.simulate("change");

      expect(props.onChange).toHaveBeenCalledTimes(1);
      // Read the event passed into the onChange function
      expect(props.onChange.mock.calls[0][0].target.value).toBe("2020-1-2");
    });

    it("combines the field values to return an event target representing the full date", () => {
      // We need to mount the component so the input values can be accessed
      const mountComponent = true;

      const { props, wrapper } = render(
        {
          name: "full-date-field",
          onChange: jest.fn(),
          value: "2020-07-04",
        },
        mountComponent
      );

      wrapper
        .find("input") // since we mount the component, this is input rather than InputText
        .first()
        .simulate("change");

      expect(props.onChange).toHaveBeenCalledTimes(1);
      // Read the event passed into the onChange function
      expect(props.onChange.mock.calls[0][0].target.value).toBe("2020-07-04");
    });
  });

  describe("when errorMsg is set", () => {
    it("passes errorMsg to FormLabel", () => {
      const { props, wrapper } = render({ errorMsg: "Oh no." });

      expect(wrapper.find("FormLabel").prop("errorMsg")).toBe(props.errorMsg);
    });

    it("adds error classes to the form group", () => {
      const { wrapper } = render({ errorMsg: "Oh no." });
      const formGroup = wrapper.find(".usa-form-group");

      expect(formGroup.hasClass("usa-form-group--error")).toBe(true);
    });
  });

  describe("when `smallLabel` is true", () => {
    it("sets the FormLabel small prop to true", () => {
      const { wrapper } = render({ smallLabel: true });
      const label = wrapper.find("FormLabel");

      expect(label.prop("small")).toBe(true);
    });
  });

  describe("when dayInvalid is true", () => {
    it("adds error class to the day input component", () => {
      const { wrapper } = render({ dayInvalid: true });

      const field = wrapper.find("InputText").at(1);

      expect(field.prop("inputClassName")).toMatch("usa-input--error");
    });
  });

  describe("when monthInvalid is true", () => {
    it("adds error class to the month input component", () => {
      const { wrapper } = render({ monthInvalid: true });

      const field = wrapper.find("InputText").at(0);

      expect(field.prop("inputClassName")).toMatch("usa-input--error");
    });
  });

  describe("when yearInvalid is true", () => {
    it("adds error class to the year input component", () => {
      const { wrapper } = render({ yearInvalid: true });

      const field = wrapper.find("InputText").at(2);

      expect(field.prop("inputClassName")).toMatch("usa-input--error");
    });
  });
});

describe("formatFieldsAsISO8601", () => {
  it("outputs ISO 8601 date string", () => {
    const result = formatFieldsAsISO8601({
      month: "12",
      day: "10",
      year: "1985",
    });

    expect(result).toBe("1985-12-10");
  });

  it("adds leading zero to month and day when their length is 1", () => {
    const result = formatFieldsAsISO8601({
      month: "1",
      day: "2",
      year: "1985",
    });

    expect(result).toBe("1985-01-02");
  });

  it("does not add a leading zero to month and day when their length is 0", () => {
    const result = formatFieldsAsISO8601({
      month: "",
      day: "",
      year: "1985",
    });

    expect(result).toBe("1985--");
  });

  it("doesn't ever add a leading zero to the year", () => {
    const result = formatFieldsAsISO8601({
      month: "1",
      day: "2",
      year: "19",
    });

    expect(result).toBe("19-01-02");
  });

  it("doesn't require each date part to be set", () => {
    const result = formatFieldsAsISO8601({ day: "", year: "" });

    expect(result).toBe("");
  });

  it("returns empty string when non-digits are entered", () => {
    const result = formatFieldsAsISO8601({
      month: "a!",
      day: "b_",
      year: "c.",
    });

    expect(result).toBe("");
  });
});

describe("parseDateParts", () => {
  it("returns object with month, day, and year entries", () => {
    const result = parseDateParts("1985-12-10");

    expect(result).toEqual({ month: "12", day: "10", year: "1985" });
  });

  it("supports leading zeros from month and day", () => {
    const result = parseDateParts("1985-01-02");

    expect(result).toEqual({ month: "01", day: "02", year: "1985" });
  });

  it("removes whitespace from the date parts", () => {
    const result = parseDateParts(" 1985 - 10 - 11");

    expect(result).toEqual({ month: "10", day: "11", year: "1985" });
  });

  describe("when all date parts are empty", () => {
    it("sets date part values to empty strings", () => {
      const result = parseDateParts("--");

      expect(result).toEqual({ month: "", day: "", year: "" });
    });
  });

  describe("when the value is empty", () => {
    it("sets date part values to empty strings", () => {
      const result = parseDateParts("");

      expect(result).toEqual({ month: "", day: "", year: "" });
    });
  });

  describe("when the value is null", () => {
    it("sets date part values to empty strings", () => {
      const result = parseDateParts(null);

      expect(result).toEqual({ month: "", day: "", year: "" });
    });
  });
});
