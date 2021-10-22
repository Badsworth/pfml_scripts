import { uniqueId } from "lodash";

/**
 * Provides a consistent interface for creating error messages displayed to the user.
 * @property [field] - Path of the field the error is associated with
 * @property key - Unique key used for React `key` prop (https://reactjs.org/docs/lists-and-keys.html)
 * @property message - Internationalized message displayed to the user (like `Error#message`)
 * @property [name] - Name of the error (like `Error#name`)
 * @property [meta] - Additional error data, like the application_id associated with it
 * @property [rule] - Name of validation issue rule (e.g "min_leave_periods", "conditional", etc)
 * @property [type] - Name of validation issue type (e.g "required", "pattern", "date", etc)
 */
class AppErrorInfo {
  key: string = uniqueId("AppErrorInfo");
  message: string | JSX.Element | null = null;
  name: string | null = null;
  field: string | null = null;
  meta: Record<string, unknown> | null = null;
  rule: string | null = null;
  type: string | null = null;

  constructor(attrs: Partial<AppErrorInfo>) {
    Object.assign(this, attrs);
  }
}

export default AppErrorInfo;
