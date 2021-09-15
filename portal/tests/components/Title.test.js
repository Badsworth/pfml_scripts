import { render, screen } from "@testing-library/react";
import React from "react";
import Title from "../../src/components/Title";

jest.mock("react-helmet", () => {
  // Render <title> directly in document.body so we can assert its value
  return { Helmet: ({ children }) => children };
});

describe("Title", () => {
  it("renders an <h1> by default", () => {
    render(<Title>Hello world</Title>);

    expect(
      screen.getByRole("heading", { name: "Hello world", level: 1 })
    ).toBeInTheDocument();
  });

  it("sets the page title", () => {
    render(<Title>Hello world</Title>);

    expect(document.title).toBe("Hello world");
  });

  it("supports setting a custom the page title", () => {
    render(<Title seoTitle="Custom page title">Hello world</Title>);

    expect(document.title).toBe("Custom page title");
  });

  it("adds a tabIndex and js-title class to the heading so we can manually move user focus to it", () => {
    render(<Title>Hello world</Title>);
    const heading = screen.getByRole("heading");

    expect(heading).toHaveClass("js-title");
    expect(heading.tabIndex).toBe(-1);
  });

  it("overrides the default bottom margin when the `bottomMargin` prop is set", () => {
    render(<Title marginBottom="4">Hello world</Title>);

    expect(screen.getByRole("heading")).toHaveClass("margin-bottom-4");
  });

  it("renders a <legend> when the `component` prop is set to 'legend'", () => {
    const { container } = render(<Title component="legend">Hello world</Title>);

    expect(container.querySelector("legend")).toHaveClass("usa-legend");
  });

  it("visually hides the heading when the `hidden` prop is set to true", () => {
    render(<Title hidden>Hello world</Title>);
    expect(screen.getByRole("heading")).toHaveClass("usa-sr-only");
  });

  it("adds classes for a smaller type size when `small` prop is true", () => {
    render(<Title small>Hello world</Title>);

    expect(screen.getByRole("heading")).toHaveClass(
      "font-heading-sm line-height-sans-3"
    );
  });
});
