import InputDate, {
  formatFieldsAsISO8601,
  parseDateParts,
} from "../../src/components/InputDate";
import { render, screen } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";

function setup(customProps = {}) {
  const props = Object.assign(
    {
      label: "Field Label",
      dayLabel: "Day",
      monthLabel: "Month",
      name: "field-name",
      yearLabel: "Year",
    },
    customProps
  );

  // Setup state management so we can test event handlers
  const InputDateWithState = () => {
    const [value, setValue] = React.useState(props.value);
    const handleChange = (event) => {
      setValue(event.target.value);
      props.onChange(event);
    };

    return <InputDate {...props} value={value} onChange={handleChange} />;
  };

  return render(<InputDateWithState />);
}

describe("InputDate", () => {
  it("renders separate fields for month / day / year", () => {
    setup({
      dayLabel: "Test Day",
      monthLabel: "Test Month",
      yearLabel: "Test Year",
    });

    expect(
      screen.getByRole("textbox", { name: "Test Day" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Test Month" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Test Year" })
    ).toBeInTheDocument();
  });

  it("renders a fieldset with a legend", () => {
    setup({ label: "Date of birth" });

    expect(
      screen.getByRole("group", { name: "Date of birth" })
    ).toBeInTheDocument();
  });

  it("supports setting the Optional text in the label", () => {
    setup({ optionalText: "Optional" });

    expect(
      screen.getByRole("group", { name: /optional/i })
    ).toBeInTheDocument();
  });

  it("breaks apart the full date value to set the month/day/year field values", () => {
    setup({
      value: "2020-10-04",
    });
    const fields = screen.getAllByRole("textbox");

    // Month
    expect(fields[0]).toHaveValue("10");
    // Day
    expect(fields[1]).toHaveValue("04");
    // Year
    expect(fields[2]).toHaveValue("2020");
  });

  it("adds leading zero to month and day only when value is 1-digit and is blurred", () => {
    const onChange = jest.fn();
    setup({
      onChange,
      value: "2020--",
    });
    const [monthInput, dayInput, yearInput] = screen.getAllByRole("textbox");

    const getLastChangeEventValue = () => {
      // Access the event argument this way instead of toHaveBeenCalledWith()
      // to workaround warnings related to https://fb.me/react-event-pooling
      return onChange.mock.calls[onChange.mock.calls.length - 1][0].target
        .value;
    };

    userEvent.type(monthInput, "1");
    expect(getLastChangeEventValue()).toBe("2020-1-");
    monthInput.blur();
    expect(getLastChangeEventValue()).toBe("2020-01-");

    userEvent.type(dayInput, "2");
    expect(getLastChangeEventValue()).toBe("2020-01-2");
    dayInput.blur();
    expect(getLastChangeEventValue()).toBe("2020-01-02");

    // No leading zero on year
    userEvent.clear(yearInput);
    userEvent.type(yearInput, "1990");
    expect(getLastChangeEventValue()).toBe("1990-01-02");
    yearInput.blur();
    expect(getLastChangeEventValue()).toBe("1990-01-02");

    // No leading zero when the value is already two digits
    userEvent.clear(dayInput);
    userEvent.type(dayInput, "30");
    expect(getLastChangeEventValue()).toBe("1990-01-30");
    dayInput.blur();
    expect(getLastChangeEventValue()).toBe("1990-01-30");
  });

  it("supports inline error message and styling", () => {
    const { container } = setup({ errorMsg: "Oh no" });

    expect(screen.getByText("Oh no")).toBeInTheDocument();
    expect(container.firstChild).toHaveClass("usa-form-group--error");
  });

  it("supports error styling for day/month/year fields", () => {
    setup({
      errorMsg: "Oh no",
      dayInvalid: true,
      monthInvalid: true,
      yearInvalid: true,
    });

    const [monthInput, dayInput, yearInput] = screen.getAllByRole("textbox");

    expect(monthInput).toHaveClass("usa-input--error");
    expect(dayInput).toHaveClass("usa-input--error");
    expect(yearInput).toHaveClass("usa-input--error");
  });

  it("supports the small label variation", () => {
    setup({ smallLabel: true, label: "Field label" });
    const label = screen.getByText("Field label");

    expect(label).toHaveClass("font-heading-xs");
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
