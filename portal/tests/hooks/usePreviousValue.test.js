import { act, renderHook } from "@testing-library/react-hooks";
import usePreviousValue from "../../src/hooks/usePreviousValue";
import { useState } from "react";

describe("usePreviousValue", () => {
  it("returns the previous value when the value changes", () => {
    let previousValue, setValue, value;

    renderHook(() => {
      [value, setValue] = useState("a");
      previousValue = usePreviousValue(value);
    });

    act(() => {
      setValue("b");
    });

    expect(previousValue).toBe("a");

    act(() => {
      setValue("c");
    });

    expect(previousValue).toBe("b");
  });
});
