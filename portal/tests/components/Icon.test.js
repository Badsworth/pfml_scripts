import Icon from "../../src/components/Icon";
import React from "react";
import { render } from "@testing-library/react";

describe("Icon", () => {
  it("renders the component", () => {
    const { container } = render(<Icon name="edit" />);
    expect(container.firstChild).toMatchInlineSnapshot(`
      <svg
        aria-hidden="true"
        class="usa-icon"
        focusable="false"
        role="img"
      >
        <use
          xlink:href="/img/sprite.svg#edit"
        />
      </svg>
    `);
  });

  it("adds the className to the icon as needed", () => {
    const { container } = render(<Icon name="edit" className="custom-class" />);
    expect(container.firstChild).toHaveClass("custom-class");
  });

  it('adds "fill" to the svg as needed', () => {
    const { container } = render(<Icon name="edit" fill="currentColor" />);
    expect(container.firstChild).toHaveAttribute("fill", "currentColor");
  });

  it("can pass through size to the className", () => {
    const { container } = render(<Icon name="edit" size={4} />);
    expect(container.firstChild).toHaveClass("usa-icon--size-4");
  });
});
