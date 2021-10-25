import { render, screen } from "@testing-library/react";
import React from "react";
import Spinner from "../../src/components/Spinner";

describe("Spinner", () => {
  it("renders spinner with the given aria text", () => {
    const text = "Loading!";

    render(<Spinner aria-valuetext={text} />);

    expect(screen.getByRole("progressbar")).toMatchInlineSnapshot(`
<span
  aria-valuetext="Loading!"
  class="c-spinner"
  role="progressbar"
/>
`);
  });

  it("renders a small spinner when small prop is passed", () => {
    render(<Spinner aria-valuetext="Loading!" small />);

    expect(screen.getByRole("progressbar")).toHaveClass("height-3 width-3");
  });
});
