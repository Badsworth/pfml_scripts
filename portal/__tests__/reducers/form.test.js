import { updateField, updateFields } from "../../src/actions";
import formReducer from "../../src/reducers/form";

describe("form reducer", () => {
  describe("UPDATE_FIELD", () => {
    it("updates a field value", () => {
      const initialState = {};
      const fieldName = "name";
      const value = "value";
      const action = updateField(fieldName, value);

      expect(formReducer(initialState, action)).toEqual({
        [fieldName]: value,
      });
    });
  });

  describe("UPDATE_FIELDS", () => {
    it("updates multiple fields", () => {
      const initialState = { name0: "value0" };
      const values = {
        name1: "value1",
        name2: "value2",
      };
      const action = updateFields(values);

      expect(formReducer(initialState, action)).toEqual({
        name0: "value0",
        ...values,
      });
    });
  });
});
