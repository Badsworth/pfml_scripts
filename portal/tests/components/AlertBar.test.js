import { render, screen } from "@testing-library/react";
import AlertBar from "../../src/components/AlertBar";
import React from "react";

describe("AlertBar", () => {
  it("renders the children as the alert body text", () => {
    const { container } = render(<AlertBar>This is your alert</AlertBar>);
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.getByText(/This is your alert/)).toBeInTheDocument();
  });
});
