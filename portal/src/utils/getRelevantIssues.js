import { compact, find, map } from "lodash";

/**
 * Combines API errors and warnings into a single array of issues.
 * Optionally filters warnings based on field names.
 * @param {Array<object>} errors
 * @param {Array<{object}>} warnings
 * @param {Array<{meta: {applicableRules: string[], fields: string[]}}>} [pages] - Page state nodes, which
 *  when present will be used to filter warnings to only those with matching `applicableRules` or `fields`
 * @returns {Array<object>} Combination of errors and relevant warnings
 */
function getRelevantIssues(errors = [], warnings = [], pages = []) {
  let relevantWarnings = warnings;

  if (warnings.length && pages.length) {
    const applicableRules = compact(map(pages, "meta.applicableRules").flat());

    // Get the array of fields from each page, and output a single array of all those fields
    // [["firstName", "last_name"], ["ssn"]] => ["firstName", "last_name", "ssn"]
    let fields = map(pages, "meta.fields").flat();

    // Remove falsy values, which may occur if a page didn't include a set of fields,
    // then remove the model prefix:
    fields = compact(fields).map((field) => {
      // Our pages export fields prefixed with the model, but the warnings
      // won't include that prefix, so we trim it here:
      return field.replace(/^claim./, "");
    });

    relevantWarnings = warnings.filter(({ field, rule }) => {
      return applicableRules.includes(rule) || fields.includes(field);
    });
  }

  // All `errors` are considered "relevant" since they indicate
  // something was wrong with whatever was included in the request
  let issues = errors.concat(relevantWarnings);

  // When we have a disallow_hybrid_intermittent_leave issue, then we don't
  // show intermittent leave field-level issues since those are redundant
  // and likely confusing if shown
  if (find(issues, { rule: "disallow_hybrid_intermittent_leave" })) {
    issues = issues.filter(({ field = "" }) => {
      return !field.startsWith("leave_details.intermittent_leave_periods[0]");
    });
  }

  return issues;
}

export default getRelevantIssues;
