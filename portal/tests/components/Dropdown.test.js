import { render, screen } from "@testing-library/react";
import Dropdown from "../../src/components/Dropdown";
import React from "react";
import userEvent from "@testing-library/user-event";

const renderComponent = (customProps = {}) => {
  const props = {
    choices: [
      {
        label: "Apple",
        value: "a",
      },
      {
        label: "Banana",
        value: "b",
      },
    ],
    emptyChoiceLabel: "Select an answer",
    label: "Field Label",
    name: "field-name",
    onChange: jest.fn(),
    ...customProps,
  };
  return render(<Dropdown {...props} />);
};

describe("Dropdown", () => {
  it("renders select field with list of options", () => {
    renderComponent();
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toMatchSnapshot();
    const [placeholder, optionOne, optionTwo] = screen.getAllByRole("option");
    expect(placeholder).toHaveTextContent("Select an answer");
    expect(optionOne).toHaveValue("a");
    expect(optionTwo).toHaveValue("b");
    expect(screen.getByRole("combobox")).toHaveAccessibleName("Field Label");
  });

  it("enables users to select an option from the dropdown", () => {
    const onChange = jest.fn();
    renderComponent({ onChange });
    userEvent.selectOptions(screen.getByRole("combobox"), ["a"]);
    expect(onChange).toHaveBeenCalled();
  });

  it("can display optionalText in the form label", () => {
    renderComponent({ optionalText: "(optional)" });
    expect(
      screen.getByRole("combobox", { name: "Field Label (optional)" })
    ).toBeInTheDocument();
  });

  it("can display a hint in the form label", () => {
    renderComponent({ hint: "this is a pro tip" });

    expect(
      screen.getByRole("combobox", { name: /this is a pro tip/i })
    ).toBeInTheDocument();
  });

  it("can render the label small", () => {
    renderComponent({ smallLabel: true });
    const label = screen.getByText(/Field Label/);
    expect(label).toHaveClass("usa-label text-bold font-heading-xs measure-5");
  });

  it("can handle errors", () => {
    renderComponent({ errorMsg: "Oh no" });
    const select = screen.getByRole("combobox");
    expect(select).toHaveClass("usa-input--error");
    expect(screen.getByText(/Oh no/)).toBeInTheDocument();
  });

  it("when autocomplete is true, user can click input to see dropdown values", () => {
    renderComponent({ autocomplete: true });
    const input = screen.getByRole("combobox");
    expect(screen.queryByRole("option")).not.toBeInTheDocument();
    userEvent.click(input);
    expect(screen.getAllByRole("option")).toHaveLength(2);
  });

  it("when autocomplete is true, users have option to close out via x in ui", () => {
    renderComponent({ autocomplete: true });
    const [clearButton, toggleDropDownbtn] = screen.getAllByRole("button");
    expect(clearButton).toBeInTheDocument();
    expect(toggleDropDownbtn).toBeInTheDocument();
  });
});
