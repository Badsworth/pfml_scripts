import { render, screen } from "@testing-library/react";
import InputAbsenceCaseId from "../../src/components/InputAbsenceCaseId";
import React from "react";
import userEvent from "@testing-library/user-event";

function setup(customProps = {}) {
  const props = Object.assign(
    {
      label: "Application ID",
      name: "case_id",
    },
    customProps
  );

  function ControlledInputAbsenceCaseId() {
    const [value, setValue] = React.useState("");
    return (
      <InputAbsenceCaseId
        {...props}
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
    );
  }

  return render(<ControlledInputAbsenceCaseId />);
}

describe("InputAbsenceCaseId", () => {
  it("accepts empty value", () => {
    setup();
    const field = screen.getByRole("textbox");

    userEvent.type(field, " ");
    userEvent.tab();

    expect(field).toHaveValue("");
  });

  it("transforms value to uppercase, inserts dashes around digits, and trims whitespace/periods when blurred", () => {
    setup();
    const field = screen.getByRole("textbox");

    userEvent.type(field, "ntn123456abs01 ");
    expect(field).toHaveValue("ntn123456abs01 ");

    userEvent.tab();
    expect(field).toHaveValue("NTN-123456-ABS-01");

    userEvent.clear(field);
    userEvent.type(field, "ntn 123 abs 01");
    userEvent.tab();

    expect(field).toHaveValue("NTN-123-ABS-01");

    userEvent.clear(field);
    userEvent.type(field, "NTN-124-ABS-01.");
    userEvent.tab();

    expect(field).toHaveValue("NTN-124-ABS-01");
  });

  it("accepts value in expected format", () => {
    setup();
    const field = screen.getByRole("textbox");

    userEvent.type(field, "NTN-123456-ABS-01");
    userEvent.tab();

    expect(field).toHaveValue("NTN-123456-ABS-01");
  });

  it("doesn't insert dashes when not in the expected format", () => {
    setup();
    const field = screen.getByRole("textbox");

    userEvent.type(field, "abc123456");
    userEvent.tab();

    expect(field).toHaveValue("ABC123456");
  });
});
