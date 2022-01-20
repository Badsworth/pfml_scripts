import { render, screen } from "@testing-library/react";
import InputPassword from "../../src/components/InputPassword";
import React from "react";
import userEvent from "@testing-library/user-event";

function renderComponent(customProps = {}) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn(),
    },
    customProps
  );
  return render(<InputPassword {...props} />);
}

describe("InputPassword", () => {
  it("defaults to a password input", () => {
    renderComponent();
    expect(screen.getByLabelText("Field Label")).toHaveAttribute(
      "type",
      "password"
    );
  });

  it("when checkbox is clicked, toggles the input type", () => {
    renderComponent();
    expect(screen.getByLabelText("Field Label")).toHaveAttribute(
      "type",
      "password"
    );
    userEvent.click(screen.getByRole("checkbox", { name: /Show password/i }));
    expect(screen.getByLabelText("Field Label")).toHaveAttribute(
      "type",
      "text"
    );
  });

  it("generates a unique id", () => {
    renderComponent({ name: "one" });
    renderComponent({ name: "two" });

    const idRegex = /InputPassword[0-9]+/;
    const [fieldOne, fieldTwo] = screen.getAllByLabelText("Field Label");

    expect(fieldOne.id).toMatch(idRegex);
    expect(fieldOne.id).not.toBe(fieldTwo.id);
  });
});
