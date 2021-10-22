import HeadingPrefix from "../../src/components/HeadingPrefix";
import React from "react";
import { render } from "@testing-library/react";

describe("HeadingPrefix", () => {
  it("renders span with expected classes", () => {
    const { container } = render(<HeadingPrefix>Part 1</HeadingPrefix>);

    expect(container.firstChild).toMatchInlineSnapshot(`
      <span
        class="display-block font-heading-2xs margin-bottom-2 text-base-dark text-bold"
      >
        Part 1
      </span>
    `);
  });
});
