import { fireEvent, render, screen } from "@testing-library/react";
import Button from "../../src/components/Button";
import React from "react";

// TODO (CP-2492) - refine these patterns, including aria / a11y testing
describe("Button", () => {
  it("renders the button with default styling", () => {
    const { container } = render(<Button>Button label</Button>);
    expect(container.firstChild).toMatchInlineSnapshot(`
      <button
        class="usa-button position-relative"
        type="button"
      >
        Button label
      </button>
    `);
    expect(screen.getByText(/Button label/)).toBeTruthy();
  });

  it("variation passes through with impact on class styles", () => {
    const { container } = render(
      <Button variation="outline">Hello world</Button>
    );
    expect(container.firstChild.className).toEqual(
      "usa-button position-relative usa-button--outline bg-white"
    );
  });

  it("inversed passes through with impact on class styles", () => {
    const { container } = render(<Button inversed={true}>Hello world</Button>);
    expect(container.firstChild.className).toEqual(
      "usa-button position-relative usa-button--inverse"
    );
  });

  it("loading state disables button and displays loading spinner", () => {
    const onClickHandler = jest.fn();
    render(
      <Button
        loading={true}
        onClick={onClickHandler}
        loadingMessage="loading message"
      >
        Click me I dare you
      </Button>
    );
    expect(screen.findByRole("progressbar")).toBeTruthy();
    expect(screen.getByText(/loading message/)).toBeTruthy();
    fireEvent.click(screen.getByText(/Click me I dare you/));
    expect(onClickHandler).not.toHaveBeenCalled();
  });
});
