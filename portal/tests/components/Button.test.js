import { render, screen } from "@testing-library/react";
import Button from "../../src/components/Button";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("Button", () => {
  it("renders the button with default styling", () => {
    render(<Button>Button label</Button>);
    const button = screen.getByRole("button", { name: /Button label/ });
    expect(button).toMatchInlineSnapshot(`
      <button
        class="usa-button position-relative"
        type="button"
      >
        Button label
      </button>
    `);
    expect(button).toHaveAccessibleName("Button label");
  });

  it("calls on click handler as expected", () => {
    const onClickHandler = jest.fn();
    render(<Button onClick={onClickHandler}>Click me</Button>);
    userEvent.click(screen.getByText(/Click me/));
    expect(onClickHandler).toHaveBeenCalled();
  });

  it("button is not clickable with disabled prop is passed in", () => {
    const onClickHandler = jest.fn();
    render(
      <Button disabled={true} onClick={onClickHandler}>
        Just try to click me
      </Button>
    );
    const button = screen.getByRole("button");
    userEvent.click(button);
    expect(onClickHandler).not.toHaveBeenCalled();
    expect(button).toBeDisabled();
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
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getByText(/loading message/)).toBeInTheDocument();
    userEvent.click(screen.getByText(/Click me I dare you/));
    expect(onClickHandler).not.toHaveBeenCalled();
  });

  it("can receive styling variations that take effect", () => {
    render(<Button variation="outline">Hello world</Button>);
    expect(screen.getByRole("button")).toHaveClass(
      "usa-button position-relative usa-button--outline bg-white"
    );
  });

  it("inversed passes through with impact on class styles", () => {
    render(<Button inversed={true}>Hello world</Button>);
    expect(screen.getByRole("button")).toHaveClass(
      "usa-button position-relative usa-button--inverse"
    );
  });

  it("can pass through submit type", () => {
    render(<Button type="submit">Submit</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("type", "submit");
  });

  it("supports aria-label", () => {
    render(<Button aria-label="Save and continue">Submit</Button>);

    expect(
      screen.getByRole("button", { name: "Save and continue" })
    ).toBeInTheDocument();
  });
});
