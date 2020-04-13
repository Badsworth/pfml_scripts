import { removeField, updateFields } from "../../src/actions";
import formReducer from "../../src/reducers/form";

describe("form reducer", () => {
  describe("UPDATE_FIELDS", () => {
    it("updates multiple fields without mutating state", () => {
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
      expect(initialState).toEqual({ name0: "value0" });
    });
  });

  describe("REMOVE_FIELD", () => {
    it("Removes field from state without mutating state", () => {
      const initialState = { name: "value", name2: "value2" };
      const fieldName = "name";
      const action = removeField(fieldName);

      expect(formReducer(initialState, action)).toEqual({ name2: "value2" });
      expect(initialState).toEqual({ name: "value", name2: "value2" });
    });
  });
});
