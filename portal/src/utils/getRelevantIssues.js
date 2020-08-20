import { get } from "lodash";

/**
 * Combines API errors and warnings into a single array of issues.
 * Optionally filters warnings based on field names.
 * @param {Array<object>} errors
 * @param {Array<object>} warnings
 * @param {object} [filterData] - If present, only warnings with a matching field
 * in this data will be returned in the list of issues.
 * @returns {Array<object>} Combination of errors and relevant warnings
 */
function getRelevantIssues(errors = [], warnings = [], filterData) {
  let relevantWarnings = warnings;

  if (warnings.length && filterData) {
    relevantWarnings = warnings.filter(({ field }) => {
      // field is a path (e.g leave_details.employer_notified)
      // so we use get() as a nifty/hacky way to identify whether
      // the filterData includes this field
      return get(filterData, field) !== undefined;
    });
  }

  // All `errors` are considered "relevant" since they indicate
  // something was wrong with whatever was included in the request
  return errors.concat(relevantWarnings);
}

export default getRelevantIssues;
