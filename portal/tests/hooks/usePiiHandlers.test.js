import { createInputElement, testHook } from "../test-utils";
import usePiiHandlers from "../../src/hooks/usePiiHandlers";

describe("usePiiHandlers", () => {
  let event, handleBlur, handleFocus, props;
  const initialValue = "xxx-xx-xxxx";

  beforeEach(() => {
    props = {
      name: "name",
      value: initialValue,
      type: "text",
      onChange: jest.fn(),
      onBlur: jest.fn(),
      onFocus: jest.fn(),
    };

    testHook(() => {
      ({ handleBlur, handleFocus } = usePiiHandlers(props));
    });

    event = {
      target: createInputElement({ value: "test event" }),
    };
  });

  describe("handleBlur", () => {
    it("calls original blur with event", () => {
      handleBlur(event);

      expect(props.onBlur).toHaveBeenCalledWith(event);
    });

    it("resets to initialValue if value is blank", () => {
      props.value = "";

      handleBlur(event);

      expect(props.onChange.mock.calls[0][0].target.value).toBe(initialValue);
    });

    it("does not reset to initialValue if value is present", () => {
      handleBlur(event);
      expect(props.onChange).toHaveBeenCalledTimes(0);
    });
  });

  describe("handleFocus", () => {
    it("calls original focus with event", () => {
      handleFocus(event);

      expect(props.onFocus).toHaveBeenCalledWith(event);
    });

    it("clears value on first call", () => {
      handleFocus(event);

      expect(props.onChange.mock.calls[0][0].target.value).toBe("");
    });

    it("does not clear value on subsequent calls", () => {
      handleFocus(event);
      handleFocus(event);
      expect(props.onChange).toHaveBeenCalledTimes(1);
    });

    it("clears value if value was reset with blur", () => {
      handleFocus(event);
      props.value = "";
      handleBlur(event);
      props.value = "999-99-999";
      handleFocus(event);
      expect(props.onChange).toHaveBeenCalledTimes(3);
      expect(props.onChange.mock.calls[2][0]).toEqual({
        _originalEvent: event,
        target: expect.objectContaining({ value: "" }),
      });
    });
  });
});
