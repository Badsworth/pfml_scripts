import { render, screen } from "@testing-library/react";
import AddButton from "../../../src/components/employers/AddButton";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("AddButton", () => {
  it("renders the component", () => {
    render(<AddButton label="Add new benefit" onClick={jest.fn()} />);

    expect(screen.getByRole("button")).toMatchSnapshot();
  });

  it("disables the button", () => {
    render(<AddButton label="Add new benefit" onClick={jest.fn()} disabled />);

    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("triggers onClick", () => {
    const onClick = jest.fn();
    render(<AddButton label="Add new benefit" onClick={onClick} />);

    userEvent.click(screen.getByRole("button"));

    expect(onClick).toHaveBeenCalled();
  });
});
