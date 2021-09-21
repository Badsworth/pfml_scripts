import { act, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { renderHook } from "@testing-library/react-hooks";
import useThrottledHandler from "../../src/hooks/useThrottledHandler";
import userEvent from "@testing-library/user-event";

describe("useThrottledHandler", () => {
  let Component, handler, throttleHandler;

  beforeEach(() => {
    handler = jest.fn().mockResolvedValueOnce(null);
    Component = (props) => {
      throttleHandler = useThrottledHandler(props.handler);
      return <button type="button" onClick={throttleHandler} />;
    };

    render(
      <Component
        handler={async () => {
          await handler();
        }}
      />
    );
  });

  it("does not call handler simultaneously", async () => {
    userEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(handler).toHaveBeenCalledTimes(1);
      expect(throttleHandler.isThrottled).toBe(false);
    });
  });

  it("sets throttleHandler.isThrottled to true during call", async () => {
    userEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(throttleHandler.isThrottled).toBe(true);
    });
  });

  it("does not reset state if component is unmounted", async () => {
    const HiddenComponent = (props) => {
      return (
        <div>
          {!props.hide && (
            <Component
              handler={async () => {
                await handler();
              }}
            />
          )}
        </div>
      );
    };

    const { rerender } = render(<HiddenComponent />);
    userEvent.click(screen.getAllByRole("button")[1]);
    rerender(<HiddenComponent hide={true} />);

    await waitFor(() => {
      expect(throttleHandler.isThrottled).toBe(true);
    });
  });

  it("rejects handlers that do no return a promise", () => {
    let handler;
    renderHook(() => {
      const nonAsyncHandler = () => {};
      handler = useThrottledHandler(nonAsyncHandler);
    });

    return expect(act(handler)).rejects.toThrow();
  });
});
