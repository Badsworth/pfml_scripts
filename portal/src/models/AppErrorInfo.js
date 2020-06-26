import BaseModel from "./BaseModel";
import uniqueId from "lodash/uniqueId";

/**
 * Provides a consistent interface for creating error and warning messages that
 * will be displayed to the user.
 * TODO: Once there's clarity on the shape of API errors, we can align
 * this model to better match the API conventions.
 */
class AppErrorInfo extends BaseModel {
  get defaults() {
    return {
      key: uniqueId("AppErrorInfo"), // Necessary for: https://reactjs.org/docs/lists-and-keys.html
      message: null,
      type: null,
      field: null, // if error is returned from API
    };
  }
}

export default AppErrorInfo;
