/**
 * Reducer for the form being actively edited, which may span multiple pages.
 * @param {object} state - The current form state
 * @param {object} action - Must contain at least a `type` property
 * @returns {object} Updated form state
 */
const formReducer = (state = {}, action) => {
  switch (action.type) {
    case "UPDATE_FIELD":
      return {
        ...state,
        [action.name]: action.value,
      };
    case "UPDATE_FIELDS":
      return {
        ...state,
        ...action.values,
      };
    default:
      return state;
  }
};

export default formReducer;
