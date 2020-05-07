import BaseModel from "./BaseModel";
import uniqueId from "lodash/uniqueId";

/**
 * Provides a consistent interface for creating error messages that
 * will be displayed to the user.
 * TODO: Once there's clarity on the shape of API errors, we can align
 * this model to better match the API conventions.
 */
class AppErrorInfo extends BaseModel {
  get defaults() {
    return {
      key: uniqueId("AppErrorInfo"), // Necessary for: https://reactjs.org/docs/lists-and-keys.html
      message: null,
    };
  }
}

export default AppErrorInfo;
