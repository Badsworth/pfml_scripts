/**
 * @file Redux Action creators. "Actions" are plain objects describing what happened in
 * the app, and serve as the sole way to describe an intention to mutate state.
 * This file exports "Action creators," which are functions that create actions.
 * Action creators let us decouple additional logic around dispatching an action,
 * from the actual components emitting those actions.
 *
 * Your React component should import an action creator from this file and use it
 * when you call the dispatch() function.
 *
 * For example:
 * import { myExampleActionCreator } from "./actions"
 * dispatch(myExampleActionCreator())
 *
 * @see https://redux.js.org/basics/actions
 */

/**
 * Update a form field's value stored in our state
 * @param {string} name - The name representing this field in our state
 * @param {*} value
 * @returns {object}
 */
export const updateField = (name, value) => ({
  type: "UPDATE_FIELD",
  name,
  value,
});

/**
 * Update multiple form fields
 * @param {object} values - An object of field names and values
 * @returns {object}
 */
export const updateFields = values => ({
  type: "UPDATE_FIELDS",
  values,
});

/**
 * Update a form field's value stored in our state. Similar to `updateField`,
 * but accepts a JS event object. Typically will be used in a field's onChange
 * event handler.
 * @see https://github.com/navahq/archive-vermont-customer-portal-apps/blob/27b66dd7bf37671a6e33a8d2c51a82c7bd9daa41/online-application-app/src/client/actions/index.js#L150
 * @param {object} event
 * @param {object} event.target
 * @param {boolean} [event.target.checked] - if input was radio/checkbox, was it selected?
 * @param {string} event.target.name - The name representing this field in our state
 * @param {*} event.target.value
 * @param {string} [event.target.type] - what type of input is this value coming from (i.e text, radio)
 * @returns {object}
 */
export function updateFieldFromEvent({ target }) {
  let { checked, name, type, value } = target;

  if (type === "checkbox" || type === "radio") {
    // Convert boolean input string values into an actual boolean
    switch (value) {
      case "true":
        value = checked;
        break;
      case "false":
        value = !checked;
        break;
    }
  } else if (typeof value === "string" && value.trim() === "") {
    // An empty or empty-looking string will be interpreted as valid
    // in the eyes of JSON Schema, even if marked as "required." So,
    // we want to store an empty string as `undefined` in order for a
    // required field to fail validation if its value is empty.
    value = undefined;
  }

  return updateField(name, value);
}
