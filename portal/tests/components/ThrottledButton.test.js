import { act, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import ThrottledButton from "../../src/components/ThrottledButton";
import tracker from "../../src/services/tracker";
import userEvent from "@testing-library/user-event";

describe("ThrottledButton", () => {
  it("renders the button with default styling", () => {
    render(<ThrottledButton>Button label</ThrottledButton>);
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

  it("calls on click handler", async () => {
    const onClickHandler = jest.fn(() => Promise.resolve());
    render(
      <ThrottledButton onClick={onClickHandler}>Click me</ThrottledButton>
    );
    const button = screen.getByText(/Click me/);
    await act(async () => {
      await userEvent.click(button);
    });
    expect(onClickHandler).toHaveBeenCalled();
  });

  it("when onClick handler is not a promise tracks the event", async () => {
    const trackerSpy = jest.spyOn(tracker, "trackEvent");
    const warnSpy = jest.fn();
    jest.spyOn(console, "warn").mockImplementationOnce(warnSpy);

    const onClickHandler = jest.fn();
    render(
      <ThrottledButton onClick={onClickHandler}>Click me</ThrottledButton>
    );
    const button = screen.getByText(/Click me/);
    await act(async () => {
      await userEvent.click(button);
    });
    expect(onClickHandler).toHaveBeenCalled();
    expect(trackerSpy).toHaveBeenCalledWith(
      "onClick wasn't a Promise, so user isn't seeing a loading indicator."
    );
    expect(warnSpy).toHaveBeenCalled();
  });

  it("button is not clickable when disabled prop is passed in", async () => {
    const onClickHandler = jest.fn(() => Promise.resolve());
    render(
      <ThrottledButton disabled={true} onClick={onClickHandler}>
        Just try to click me
      </ThrottledButton>
    );
    const button = screen.getByRole("button");
    await act(async () => {
      await userEvent.click(button);
    });
    expect(onClickHandler).not.toHaveBeenCalled();
    expect(button).toBeDisabled();
  });

  it("loading state disables button and displays loading spinner", async () => {
    let resolveOnClick;
    const onClickHandler = jest.fn(
      () =>
        new Promise((resolve, reject) => {
          resolveOnClick = resolve;
        })
    );
    render(
      <ThrottledButton
        onClick={onClickHandler}
        loadingMessage="loading message"
      >
        Click me I dare you
      </ThrottledButton>
    );

    const button = screen.getByRole("button");

    // Click the button but don't wait for its operation to complete
    userEvent.click(button);
    await waitFor(() => expect(onClickHandler).toHaveBeenCalled());

    // At this point the button has been clicked and has entered its
    // loading state. It will stay loading until we call resolveOnclick()
    // Verify button is in a loading state
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getByText(/loading message/)).toBeInTheDocument();
    // Verify the button can't be clicked while it's loading
    onClickHandler.mockClear();
    userEvent.click(button);
    expect(onClickHandler).not.toHaveBeenCalled();

    // Finally, resolve the onClick handler
    await act(async () => {
      await resolveOnClick();
    });
  });

  it("button is clickable again after onClick has resolved", async () => {
    const onClickHandler = jest.fn(() => Promise.resolve());
    render(
      <ThrottledButton
        onClick={onClickHandler}
        loadingMessage="loading message"
      >
        Click me twice
      </ThrottledButton>
    );

    const button = screen.getByRole("button");
    await act(async () => {
      await userEvent.click(button);
      await waitFor(() => expect(button).toBeEnabled());
      await userEvent.click(button);
    });
    expect(onClickHandler).toHaveBeenCalledTimes(2);
  });

  it("can receive styling variations that take effect", () => {
    render(<ThrottledButton variation="outline">Hello world</ThrottledButton>);
    expect(screen.getByRole("button")).toHaveClass(
      "usa-button position-relative usa-button--outline bg-white"
    );
  });

  it("inversed passes through with impact on class styles", () => {
    render(<ThrottledButton inversed={true}>Hello world</ThrottledButton>);
    expect(screen.getByRole("button")).toHaveClass(
      "usa-button position-relative usa-button--inverse"
    );
  });

  it("can pass through submit type", () => {
    render(<ThrottledButton type="submit">Submit</ThrottledButton>);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("type", "submit");
  });
});
