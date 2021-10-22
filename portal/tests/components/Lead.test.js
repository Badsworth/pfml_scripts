import { render, screen } from "@testing-library/react";
import Lead from "../../src/components/Lead";
import React from "react";

describe("Lead", () => {
  it("renders a paragraph with intro class", () => {
    const { container } = render(<Lead>Hello world</Lead>);

    expect(container.firstChild).toMatchInlineSnapshot(`
      <p
        class="usa-intro"
      >
        Hello world
      </p>
    `);
  });

  it("adds additional class names", () => {
    render(<Lead className="margin-top-6">Hello world</Lead>);

    expect(screen.getByText("Hello world")).toHaveClass(
      "usa-intro margin-top-6"
    );
  });
});
