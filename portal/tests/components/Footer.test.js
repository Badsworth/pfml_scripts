import Footer from "../../src/components/Footer";
import React from "react";
import { render } from "@testing-library/react";

describe("Footer", () => {
  it("renders footer with default settings", () => {
    const { container } = render(<Footer />);

    expect(container.firstChild).toMatchSnapshot();
  });
});
