import { render, screen } from "@testing-library/react";
import React from "react";
import UnsupportedBrowserBanner from "../../src/components/UnsupportedBrowserBanner";

describe("UnsupportedBrowserBanner", () => {
  it("renders conditional HTML comment and the banner message", () => {
    const { container } = render(<UnsupportedBrowserBanner />);

    expect(container).toMatchSnapshot();
  });

  it("adds display-block when forceRender prop is set", () => {
    render(<UnsupportedBrowserBanner forceRender />);

    expect(screen.getByRole("alert")).toHaveClass("display-block");
  });
});
