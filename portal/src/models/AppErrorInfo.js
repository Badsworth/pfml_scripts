import BaseModel from "./BaseModel";
import uniqueId from "lodash/uniqueId";

/**
 * Provides a consistent interface for creating error messages displayed to the user.
 * @property {string} [field] - Path of the field the error is associated with
 * @property {string} key - Unique key used for React `key` prop (https://reactjs.org/docs/lists-and-keys.html)
 * @property {string} message - Internationalized message displayed to the user (like `Error#message`)
 * @property {string} [name] - Name of the error (like `Error#name`)
 * @property {object} [meta] - Additional error data, like the application_id associated with it
 * @property {string} [rule] - Name of validation rule that was not fulfilled, if caused by a validation issue
 */
class AppErrorInfo extends BaseModel {
  get defaults() {
    return {
      key: uniqueId("AppErrorInfo"),
      message: null,
      name: null,
      field: null,
      meta: null,
      rule: null,
    };
  }
}

export default AppErrorInfo;
