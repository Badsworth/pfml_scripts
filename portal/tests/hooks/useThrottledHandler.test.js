import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { testHook } from "../test-utils";
import useThrottledHandler from "../../src/hooks/useThrottledHandler";

describe("useThrottledHandler", () => {
  let handler, throttleHandler, wrapper;

  beforeEach(() => {
    handler = jest.fn().mockResolvedValueOnce(null);
    const Component = (props) => {
      // eslint-disable-next-line react/prop-types
      throttleHandler = useThrottledHandler(props.handler);
      return (
        <button
          type="button"
          onClick={throttleHandler}
          loading={throttleHandler.isThrottled}
        />
      );
    };

    wrapper = shallow(
      <Component
        handler={async () => {
          await handler();
        }}
      />
    );
  });

  it("does not call handler simultaneously", async () => {
    await act(async () => {
      wrapper.find("button").simulate("click");
      await wrapper.find("button").simulate("click");
    });

    expect(handler).toHaveBeenCalledTimes(1);
    expect(throttleHandler.isThrottled).toBe(false);
  });

  it("sets throttleHandler.isThrottled to true during call", async () => {
    await act(async () => {
      await wrapper.find("button").simulate("click");
      expect(throttleHandler.isThrottled).toBe(true);
    });
  });

  it("rejects handlers that do no return a promise", () => {
    let handler;
    testHook(() => {
      const nonAsyncHandler = () => {};
      handler = useThrottledHandler(nonAsyncHandler);
    });

    return expect(act(handler)).resolves.toThrow();
  });
});
