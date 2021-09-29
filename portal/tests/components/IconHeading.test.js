import { render, screen } from "@testing-library/react";

import IconHeading from "../../src/components/IconHeading";
import React from "react";

describe("IconHeading", () => {
  it("renders IconHeading component", () => {
    render(<IconHeading name="close">Foobar</IconHeading>);
    const header = screen.getByRole("heading", { name: /foobar/i });
    const icon = screen.getByRole("img", { hidden: true });

    expect(header).toMatchSnapshot();
    expect(icon).toMatchSnapshot();
  });

  it("applies the `name` attribute correctly", () => {
    render(<IconHeading name="close">Foobar</IconHeading>);
    const icon = screen.getByRole("img", { hidden: true });
    expect(icon).toMatchInlineSnapshot(`
<svg
  aria-hidden="true"
  class="usa-icon--size-3 margin-right-2px text-red"
  fill="currentColor"
  focusable="false"
  role="img"
>
  <use
    xlink:href="/img/sprite.svg#close"
  />
</svg>
`);
  });

  it("applies the red color when name is `close`", () => {
    render(<IconHeading name="close">Foobar</IconHeading>);
    const icon = screen.getByRole("img", { hidden: true });
    expect(icon).toHaveClass("text-red");
  });

  it("applies the green color when name is `check`", () => {
    render(<IconHeading name="check">Foobar</IconHeading>);
    const icon = screen.getByRole("img", { hidden: true });
    expect(icon).toHaveClass("text-green");
  });
});
