import {
  updateField,
  updateFieldFromEvent,
  updateFields,
} from "../src/actions";

describe("Redux actions", () => {
  describe("updateField", () => {
    it("creates a Update Field action", () => {
      const name = "field";
      const value = "value";
      const expectedAction = {
        type: "UPDATE_FIELD",
        name,
        value,
      };

      expect(updateField(name, value)).toEqual(expectedAction);
    });
  });

  describe("updateFields", () => {
    it("creates an Update Fields action", () => {
      const values = {
        name1: "value1",
        name2: "value2",
      };

      const expectedAction = {
        type: "UPDATE_FIELDS",
        values,
      };

      expect(updateFields(values)).toEqual(expectedAction);
    });
  });

  describe("updateFieldFromEvent", () => {
    it("returns UPDATE_FIELD action with name and value properties", () => {
      const target = { name: "Foo", value: "Bar" };
      const result = updateFieldFromEvent({ target });

      expect(result).toMatchInlineSnapshot(`
      Object {
        "name": "Foo",
        "type": "UPDATE_FIELD",
        "value": "Bar",
      }
    `);
    });

    it("accepts 'type' property in the data argument, but doesn't include it in the action", () => {
      const target = { name: "Foo", value: "bar", type: "radio" };
      const result = updateFieldFromEvent({ target });

      expect(result.type).toBe("UPDATE_FIELD");
    });

    describe("given field type is radio", () => {
      it("converts 'true' string into a boolean", () => {
        const target = {
          checked: true,
          name: "Foo",
          value: "true",
          type: "radio",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe(true);
      });

      it("converts 'false' string into a boolean", () => {
        const target = {
          checked: true,
          name: "Foo",
          value: "false",
          type: "radio",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe(false);
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
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe(true);
      });

      it("converts 'true' string into a `false` boolean, when field is unchecked", () => {
        const target = {
          checked: false,
          name: "Foo",
          value: "true",
          type: "checkbox",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe(false);
      });

      it("converts 'false' string into a `false` boolean, when field is checked", () => {
        const target = {
          checked: true,
          name: "Foo",
          value: "false",
          type: "checkbox",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe(false);
      });

      it("converts 'false' string into a `true` boolean, when field is unchecked", () => {
        const target = {
          checked: false,
          name: "Foo",
          value: "false",
          type: "checkbox",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe(true);
      });
    });

    describe("given field type is 'text'", () => {
      it("allows trailing whitespace so people can type multiple words", () => {
        const target = {
          name: "Foo",
          type: "text",
          value: "Bar ",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBe("Bar ");
      });

      it("converts a blank string into undefined", () => {
        const target = {
          name: "Foo",
          type: "text",
          value: " ",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBeUndefined();
      });

      it("doesn't attempt to trim an undefined value", () => {
        const target = {
          name: "Foo",
          type: "text",
          value: undefined,
        };
        const result = updateFieldFromEvent({ target });

        expect(result.value).toBeUndefined();
      });
    });
  });
});
