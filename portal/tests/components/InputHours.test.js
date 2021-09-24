import { render, screen } from "@testing-library/react";
import InputHours from "../../src/components/InputHours";
import React from "react";
import { renderHook } from "@testing-library/react-hooks";
import useHandleInputChange from "../../src/hooks/useHandleInputChange";
import userEvent from "@testing-library/user-event";

function setup(customProps = {}) {
  const props = {
    label: "Label",
    hoursLabel: "Hours Label",
    minutesLabel: "Minutes Label",
    name: "field-name",
    minutesIncrement: 15,
    emptyMinutesLabel: "Select minute",
    onChange: jest.fn(),
    ...customProps,
  };

  // Setup state management so we can test event handlers
  const InputHoursWithState = () => {
    const [value, setValue] = React.useState(props.value);
    const handleChange = (event) => {
      setValue(event.target.value);
      props.onChange(event);
    };

    return <InputHours {...props} value={value} onChange={handleChange} />;
  };

  return render(<InputHoursWithState />);
}

describe("InputHours", () => {
  it("renders component", () => {
    const { container } = setup({ value: 40 * 60 + 15, label: "Work hours" });

    expect(
      screen.getByRole("group", { name: "Work hours" })
    ).toBeInTheDocument();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("tightens label spacing if smallLabel prop is true", () => {
    setup({ smallLabel: true });

    expect(screen.getByRole("textbox").parentNode).toHaveClass(
      "margin-top-105"
    );
  });

  it("supports error message and styling", () => {
    setup({ errorMsg: "Something went wrong" });

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByRole("group")).toHaveClass("usa-form-group--error");
  });

  it("adds error class to the day input component when hoursInvalid is true", () => {
    setup({ hoursInvalid: true });

    expect(screen.getByRole("textbox", { name: /Hours label/i })).toHaveClass(
      "usa-input--error"
    );
  });

  it("adds error class to the minutes input component when minutesInvalid is true", () => {
    setup({ minutesInvalid: true });

    expect(
      screen.getByRole("combobox", { name: /Minutes label/i })
    ).toHaveClass("usa-input--error");
  });

  it("sets hours value to 0 when minutes are less than 60", () => {
    setup({ value: 15 });

    expect(screen.getByRole("textbox")).toHaveValue("0");
    expect(screen.getByRole("combobox")).toHaveValue("15");
  });

  it("renders correctly with 0 minutes", () => {
    setup({ value: 60 });
    expect(screen.getByRole("textbox")).toHaveValue("1");
    expect(screen.getByRole("combobox")).toHaveValue("0");
  });

  it("renders correctly if both hours and minutes are 0", () => {
    setup({ value: 0 });
    expect(screen.getByRole("textbox")).toHaveValue("0");
    expect(screen.getByRole("combobox")).toHaveValue("0");
  });

  it("renders empty hours and minutes if value is undefined", () => {
    setup({ value: undefined });
    expect(screen.getByRole("textbox")).toHaveValue("");
    expect(screen.getByRole("combobox")).toHaveValue("");
  });

  it("logs warning if minutesIncrements is not a multiple of value", () => {
    const warnSpy = jest
      .spyOn(console, "warn")
      .mockImplementationOnce(() => {});

    setup({ value: 33, minutesIncrement: 15 });
    expect(screen.getByRole("textbox")).toHaveValue("0");
    expect(screen.getByRole("combobox")).toHaveValue("");
    expect(warnSpy).toHaveBeenCalled();
  });

  it("sets hours to 0 and preserves minutes value when hours are erased", () => {
    const onChange = jest.fn();
    setup({ value: 8 * 60 + 15, onChange });

    userEvent.clear(screen.getByRole("textbox"));

    expect(screen.getByRole("textbox")).toHaveValue("0");
    expect(screen.getByRole("combobox")).toHaveValue("15");
  });

  it("supports clearing of minutes value", () => {
    const onChange = jest.fn();
    setup({ value: 15, onChange });

    userEvent.selectOptions(screen.getByRole("combobox"), ["0"]);

    expect(screen.getByRole("combobox")).toHaveValue("0");
  });

  it("propagates valid input with useHandleInputChange", () => {
    const updateFields = jest.fn();
    let onChange;
    renderHook(() => {
      onChange = useHandleInputChange(updateFields);
    });

    setup({
      name: "minutes",
      onChange,
    });

    const input = screen.getByRole("textbox");
    userEvent.clear(input);
    userEvent.type(input, "1");

    expect(updateFields).toHaveBeenCalledTimes(1);
    expect(updateFields).toHaveBeenCalledWith(
      expect.objectContaining({
        minutes: 60,
      })
    );
  });

  it("does not propagate negative input value with useHandleInputChange", () => {
    const updateFields = jest.fn();
    let onChange;
    renderHook(() => {
      onChange = useHandleInputChange(updateFields);
    });

    setup({
      name: "minutes",
      onChange,
    });

    const input = screen.getByRole("textbox");
    userEvent.type(input, "-");

    expect(updateFields).not.toHaveBeenCalled();
  });
});
