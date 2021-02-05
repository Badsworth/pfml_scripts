import { createInputElement } from "../test-utils";
import getInputValueFromEvent from "../../src/utils/getInputValueFromEvent";

describe("getInputValueFromEvent", () => {
  describe("given field type is radio", () => {
    it("converts 'true' string into a boolean", () => {
      const target = createInputElement({
        checked: true,
        name: "Foo",
        value: "true",
        type: "radio",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(true);
    });

    it("converts 'false' string into a boolean", () => {
      const target = createInputElement({
        checked: true,
        name: "Foo",
        value: "false",
        type: "radio",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(false);
    });
  });

  describe("given field type is checkbox", () => {
    it("converts 'true' string into a `true` boolean, when field is checked", () => {
      const target = createInputElement({
        checked: true,
        name: "Foo",
        value: "true",
        type: "checkbox",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(true);
    });

    it("converts 'true' string into a `false` boolean, when field is unchecked", () => {
      const target = createInputElement({
        checked: false,
        name: "Foo",
        value: "true",
        type: "checkbox",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(false);
    });

    it("converts 'false' string into a `false` boolean, when field is checked", () => {
      const target = createInputElement({
        checked: true,
        name: "Foo",
        value: "false",
        type: "checkbox",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(false);
    });

    it("converts 'false' string into a `true` boolean, when field is unchecked", () => {
      const target = createInputElement({
        checked: false,
        name: "Foo",
        value: "false",
        type: "checkbox",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(true);
    });
  });

  describe("given field type is 'text'", () => {
    it("allows trailing whitespace so people can type multiple words", () => {
      const target = createInputElement({
        name: "Foo",
        type: "text",
        value: "Bar ",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe("Bar ");
    });

    it("converts a blank string into undefined", () => {
      const target = createInputElement({
        name: "Foo",
        type: "text",
        value: " ",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBeNull();
    });

    it("doesn't attempt to trim an undefined value", () => {
      // Mock target as plain object so we can mock an undefined value
      const target = {
        name: "Foo",
        type: "text",
        value: undefined,
        getAttribute: jest.fn(),
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBeUndefined();
    });
  });

  describe("given data-value-type is 'integer'", () => {
    it("converts string to integer, removing any decimals and commas", () => {
      const target = createInputElement({
        name: "Foo",
        value: "1,200,000.3",
        "data-value-type": "integer",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(1200000);
    });

    it("does not convert mixed strings/numbers", () => {
      const target = createInputElement({
        name: "Foo",
        value: "4hockey4",
        "data-value-type": "integer",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBe("4hockey4");
    });

    it("converts empty string to undefined", () => {
      const target = createInputElement({
        name: "Foo",
        value: " ",
        "data-value-type": "integer",
      });
      const value = getInputValueFromEvent({ target });

      expect(value).toBeNull();
    });

    it("does not convert undefined", () => {
      // Mock target as plain object so we can mock an undefined value
      const target = {
        name: "Foo",
        value: undefined,
        "data-value-type": "integer",
        getAttribute: jest.fn().mockReturnValue("integer"),
      };
      const value = getInputValueFromEvent({ target });

      expect(value).toBe(undefined);
    });

    it("does not convert null to 0", () => {
      // Mock target as plain object so we can mock a null value
      const target = {
        name: "Foo",
        value: null,
        "data-value-type": "integer",
        getAttribute: jest.fn().mockReturnValue("integer"),
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
