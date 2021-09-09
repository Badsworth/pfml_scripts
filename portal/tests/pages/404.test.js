import Page from "../../src/pages/404";
import React from "react";
import { render } from "@testing-library/react";

describe("404 page", () => {
  it("renders the page with expected content and links", () => {
    const { container } = render(<Page />);
    expect(container).toMatchSnapshot();
  });
});
