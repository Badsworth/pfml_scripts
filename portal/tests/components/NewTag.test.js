import NewTag from "../../src/components/NewTag";
import React from "react";
import { render } from "@testing-library/react";

describe("NewTag", () => {
  it("renders the component", () => {
    const { container } = render(<NewTag />);

    expect(container.firstChild).toMatchSnapshot();
  });
});
