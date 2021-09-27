/**
 * We import from /pure here in order to prevent the auto-cleanup behavior, which
 * attempts to unmount the React tree. This fails for this component with a warning
 * indicating a node is being "rendered by another copy of React", which seems to be
 * due the DOM markup being altered by the USWDS script once the component mounts.
 * https://testing-library.com/docs/react-testing-library/setup/#skipping-auto-cleanup
 */
import { render, screen } from "@testing-library/react/pure";
import React from "react";
import TooltipIcon from "../../src/components/TooltipIcon";
import userEvent from "@testing-library/user-event";

describe("TooltipIcon", () => {
  it("initializes USWDS tooltip behavior", () => {
    render(<TooltipIcon position="bottom">Hello world</TooltipIcon>);

    userEvent.hover(screen.getByText(/tip/i));

    expect(
      screen.getByRole("tooltip", { name: "Hello world" })
    ).toBeInTheDocument();
  });
});
