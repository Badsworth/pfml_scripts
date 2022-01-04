import { render, screen } from "@testing-library/react";
import React from "react";
import Spinner from "../../src/components/core/Spinner";

describe("Spinner", () => {
  it("renders spinner with the given aria text", () => {
    const text = "Loading!";

    render(<Spinner aria-label={text} />);

    expect(screen.getByRole("progressbar")).toMatchInlineSnapshot(`
<span
  aria-label="Loading!"
  class="c-spinner"
  role="progressbar"
/>
`);
  });

  it("renders a small spinner when small prop is passed", () => {
    render(<Spinner aria-label="Loading!" small />);

    expect(screen.getByRole("progressbar")).toHaveClass("height-3 width-3");
  });
});
