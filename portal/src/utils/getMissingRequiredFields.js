import { pick } from "lodash";

// Is this a basic required field error? This filters out required errors not associated to a specific field. Such as
// the "require_employer_notified" rule which looks like this:
//   { type: "required", field: null, rule: "require_employer_notified", message: "..." }
const isRequiredFieldError = (error) =>
  error.type === "required" &&
  // Must be for a specific field
  !!error.field;

/**
 * Filter down to required field errors for specific fields
 * @param {Array<AppErrorInfo>} errors
 * @returns {Array<Object>} The set of errors which are due to specific missing required fields. Only the attributes we want to log are returned
 */
export default function getMissingRequiredFields(errors) {
  return errors
    .filter(isRequiredFieldError)
    .map((error) => pick(error, ["name", "field", "meta", "rule", "type"]));
}
