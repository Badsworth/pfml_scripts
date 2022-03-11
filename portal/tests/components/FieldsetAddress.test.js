import { render, screen } from "@testing-library/react";
import FieldsetAddress from "../../src/components/FieldsetAddress";
import React from "react";
import { ValidationError } from "../../src/errors";
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
      errors={[]}
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
          errors={[]}
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
    const errors = [
      new ValidationError(
        [
          {
            field: "address.line_1",
          },
          {
            field: "address.line_2",
          },
          {
            field: "address.city",
          },
          {
            field: "address.state",
          },
          {
            field: "address.zip",
          },
        ],
        "test"
      ),
    ];
    renderComponent({ errors });

    // We don't have translations for the mock issues above, so it falls back to the default message
    expect(
      screen.getByRole("textbox", {
        name: /Address Field .+ has invalid value/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", {
        name: /Address line 2 .+ has invalid value/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: /City .+ has invalid value/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: /State .+ has invalid value/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: /ZIP .+ has invalid value/i })
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
