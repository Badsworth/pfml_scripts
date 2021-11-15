import { render, screen } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import FieldsetAddress from "../../src/components/FieldsetAddress";
import React from "react";
import userEvent from "@testing-library/user-event";

const renderComponent = (customProps = {}) => {
  const addressVal = {
    city: null,
    line_1: null,
    line_2: null,
    state: null,
    zip: null,
  };

  const { container } = render(
    <FieldsetAddress
      appErrors={new AppErrorInfoCollection()}
      label={"What is your address?"}
      name={"address"}
      onChange={jest.fn()}
      value={addressVal}
      {...customProps}
    />
  );
  return {
    container,
  };
};

describe("FieldsetAddress", () => {
  it("renders the component with null values", () => {
    const { container } = renderComponent();

    expect(container).toMatchSnapshot();
  });

  it("renders the component with existing values", () => {
    const existingValues = {
      city: "Washington",
      line_1: "1600 Pennsylvania Avenue NW",
      line_2: "Rose Garden",
      state: "DC",
      zip: "20500",
    };
    const { container } = renderComponent({ value: existingValues });

    expect(container).toMatchSnapshot();
  });

  it("formats numeric values as a ZIP+4 string when the zip is unformatted and is longer than 5 digits", () => {
    const FieldsetAddressWithState = () => {
      const [value, setValue] = React.useState({});
      const handleChange = (elem) => {
        setValue({
          ...value,
          [elem.target.name.split(".")[1]]: elem.target.value,
        });
      };

      return (
        <FieldsetAddress
          appErrors={new AppErrorInfoCollection()}
          label={"What is your address?"}
          name={"address"}
          onChange={handleChange}
          value={value}
        />
      );
    };
    render(<FieldsetAddressWithState />);

    const zipInput = screen.getByLabelText("ZIP");
    userEvent.type(zipInput, "205001234");
    userEvent.click(document.body);
    expect(zipInput).toHaveValue("20500-1234");

    userEvent.clear(zipInput);
    userEvent.type(zipInput, "20500-1234");
    userEvent.click(document.body);
    expect(zipInput).toHaveValue("20500-1234");
  });

  it("displays errors on the associated inputs when there are errors", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "address.line_1",
        message: "Address is required",
      }),
      new AppErrorInfo({
        field: "address.line_2",
        message: "Address 2 is required",
      }),
      new AppErrorInfo({
        field: "address.city",
        message: "City is required",
      }),
      new AppErrorInfo({
        field: "address.state",
        message: "State is required",
      }),
      new AppErrorInfo({
        field: "address.zip",
        message: "ZIP is required",
      }),
    ]);
    renderComponent({ appErrors });

    expect(
      screen.getByRole("textbox", { name: /Address is required/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: /Address 2 is required/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: /City is required/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: /State is required/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: /ZIP is required/i })
    ).toBeInTheDocument();
  });

  it("renders with a small label when the smallLabel prop is set", () => {
    renderComponent({ smallLabel: true });

    expect(screen.getByLabelText("City").previousSibling).toHaveClass(
      "font-heading-xs"
    );
  });

  it("renders the hint text when the hint prop is set", () => {
    const hintText = "This is a hint";
    renderComponent({ hint: hintText });

    expect(screen.getByText(hintText)).toBeInTheDocument();
  });

  it("renders alterative mailing address labels when the addressType prop is mailing", () => {
    renderComponent({ addressType: "mailing" });

    expect(screen.getByLabelText("Mailing address")).toHaveAttribute(
      "name",
      "address.line_1"
    );
  });
});
