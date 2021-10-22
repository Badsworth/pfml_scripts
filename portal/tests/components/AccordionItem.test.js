import { render, screen } from "@testing-library/react";
import AccordionItem from "../../src/components/AccordionItem";
import React from "react";
import userEvent from "@testing-library/user-event";

jest.mock("../../src/hooks/useUniqueId");

describe("AccordionItem", () => {
  it("generates id", () => {
    render(
      <AccordionItem heading="Test">
        <p>Hello world</p>
      </AccordionItem>
    );
    expect(screen.getByRole("button", { name: "Test" })).toHaveAttribute(
      "aria-controls",
      "mock-unique-id"
    );
  });

  it("is collapsed by default", () => {
    render(<AccordionItem heading="Test">Hello world</AccordionItem>);
    expect(screen.getByRole("button", { name: "Test" })).toHaveAttribute(
      "aria-expanded",
      "false"
    );
    expect(screen.getByTestId("mock-unique-id")).toHaveAttribute("hidden");
  });

  it("expands when clicked", () => {
    render(
      <AccordionItem heading="Test">
        <p>Hello world</p>
      </AccordionItem>
    );

    userEvent.click(screen.getByRole("button", { name: "Test" }));
    expect(screen.getByRole("button", { name: "Test" })).toHaveAttribute(
      "aria-expanded",
      "true"
    );
    expect(screen.getByText(/Hello world/)).toBeInTheDocument();
    expect(screen.getByTestId("mock-unique-id")).not.toHaveAttribute("hidden");
  });
});
