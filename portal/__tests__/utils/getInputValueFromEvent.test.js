import getInputValueFromEvent from "../../src/utils/getInputValueFromEvent";

describe("getInputValueFromEvent", () => {
  describe("given field type is radio", () => {
    it("converts 'true' string into a boolean", () => {
      const target = {
        checked: true,
        name: "Foo",
        value: "true",
        type: "radio",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(true);
    });

    it("converts 'false' string into a boolean", () => {
      const target = {
        checked: true,
        name: "Foo",
        value: "false",
        type: "radio",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(false);
    });
  });

  describe("given field type is checkbox", () => {
    it("converts 'true' string into a `true` boolean, when field is checked", () => {
      const target = {
        checked: true,
        name: "Foo",
        value: "true",
        type: "checkbox",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(true);
    });

    it("converts 'true' string into a `false` boolean, when field is unchecked", () => {
      const target = {
        checked: false,
        name: "Foo",
        value: "true",
        type: "checkbox",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(false);
    });

    it("converts 'false' string into a `false` boolean, when field is checked", () => {
      const target = {
        checked: true,
        name: "Foo",
        value: "false",
        type: "checkbox",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(false);
    });

    it("converts 'false' string into a `true` boolean, when field is unchecked", () => {
      const target = {
        checked: false,
        name: "Foo",
        value: "false",
        type: "checkbox",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(true);
    });
  });

  describe("given field type is 'text'", () => {
    it("allows trailing whitespace so people can type multiple words", () => {
      const target = {
        name: "Foo",
        type: "text",
        value: "Bar ",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe("Bar ");
    });

    it("converts a blank string into undefined", () => {
      const target = {
        name: "Foo",
        type: "text",
        value: " ",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBeUndefined();
    });

    it("doesn't attempt to trim an undefined value", () => {
      const target = {
        name: "Foo",
        type: "text",
        value: undefined,
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBeUndefined();
    });
  });

  describe("given field inputmode is 'numeric' and field pattern is [0-9]*", () => {
    it("converts string to number", () => {
      const target = {
        name: "Foo",
        value: "44",
        inputmode: "numeric",
        pattern: "[0-9]*",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(44);
    });

    it("does not convert mixed strings/numbers", () => {
      const target = {
        name: "Foo",
        value: "4hockey4",
        inputmode: "numeric",
        pattern: "[0-9]*",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe("4hockey4");
    });

    it("converts empty string to undefined", () => {
      const target = {
        name: "Foo",
        value: " ",
        inputmode: "numeric",
        pattern: "[0-9]*",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(undefined);
    });

    it("does not convert undefined", () => {
      const target = {
        name: "Foo",
        value: undefined,
        inputmode: "numeric",
        pattern: "[0-9]*",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(undefined);
    });

    it("does not convert null to 0", () => {
      const target = {
        name: "Foo",
        value: null,
        inputmode: "numeric",
        pattern: "[0-9]*",
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(null);
    });
  });

  describe("bad input", () => {
    it("returns undefined if no parameter is passed", () => {
      const value = getInputValueFromEvent();
      expect(value).toBeUndefined();
    });

    it("returns undefined if event has no target", () => {
      const event = {};
      const value = getInputValueFromEvent(event);
      expect(value).toBeUndefined();
    });
  });
});
