import {
  removeField,
  updateField,
  updateFieldFromEvent,
  updateFields,
} from "../src/actions";

describe("Redux actions", () => {
  describe("updateField", () => {
    it("creates a UPDATE_FIELDS action", () => {
      const name = "field";
      const value = "value";
      const expectedAction = {
        type: "UPDATE_FIELDS",
        values: { [name]: value },
      };

      expect(updateField(name, value)).toEqual(expectedAction);
    });
  });

  describe("updateFields", () => {
    it("creates an UPDATE_FIELDS action", () => {
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

  describe("removeField", () => {
    it("returns REMOVE_FIELD action with name property", () => {
      const name = "fieldName";

      const expectedAction = {
        type: "REMOVE_FIELD",
        name,
      };

      expect(removeField(name)).toEqual(expectedAction);
    });
  });

  describe("updateFieldFromEvent", () => {
    it("returns UPDATE_FIELD action with name and value properties", () => {
      const target = { name: "Foo", value: "Bar" };
      const result = updateFieldFromEvent({ target });

      expect(result).toMatchInlineSnapshot(`
      Object {
        "type": "UPDATE_FIELDS",
        "values": Object {
          "Foo": "Bar",
        },
      }
    `);
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

        expect(result.values[target.name]).toBe(true);
      });

      it("converts 'false' string into a boolean", () => {
        const target = {
          checked: true,
          name: "Foo",
          value: "false",
          type: "radio",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.values[target.name]).toBe(false);
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

        expect(result.values[target.name]).toBe(true);
      });

      it("converts 'true' string into a `false` boolean, when field is unchecked", () => {
        const target = {
          checked: false,
          name: "Foo",
          value: "true",
          type: "checkbox",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.values[target.name]).toBe(false);
      });

      it("converts 'false' string into a `false` boolean, when field is checked", () => {
        const target = {
          checked: true,
          name: "Foo",
          value: "false",
          type: "checkbox",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.values[target.name]).toBe(false);
      });

      it("converts 'false' string into a `true` boolean, when field is unchecked", () => {
        const target = {
          checked: false,
          name: "Foo",
          value: "false",
          type: "checkbox",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.values[target.name]).toBe(true);
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

        expect(result.values[target.name]).toBe("Bar ");
      });

      it("converts a blank string into undefined", () => {
        const target = {
          name: "Foo",
          type: "text",
          value: " ",
        };
        const result = updateFieldFromEvent({ target });

        expect(result.values[target.name]).toBeUndefined();
      });

      it("doesn't attempt to trim an undefined value", () => {
        const target = {
          name: "Foo",
          type: "text",
          value: undefined,
        };
        const result = updateFieldFromEvent({ target });

        expect(result.values[target.name]).toBeUndefined();
      });
    });
  });
});
