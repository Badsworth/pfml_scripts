import { render, screen } from "@testing-library/react";
import AmendButton from "../../../src/components/employers/AmendButton";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("AmendButton", () => {
  it("renders the component", () => {
    render(<AmendButton />);

    expect(screen.getByRole("button")).toMatchSnapshot();
  });

  it("triggers onClick", () => {
    const handleClick = jest.fn();

    render(<AmendButton onClick={handleClick} />);
    userEvent.click(screen.getByRole("button"));

    expect(handleClick).toHaveBeenCalled();
  });
});
