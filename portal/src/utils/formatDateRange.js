import { DateTime } from "luxon";

/**
 * Format the given dates and display them as a range. Dates are
 * formatted using the user's default locale, which produces
 * internationalized, human-readable strings.
 * @param {string} startIsoDate - ISO 8601 date string
 * @param {string} endIsoDate - ISO 8601 date string
 * @returns {string}
 * @example formatDateRange("2020-09-01", "2020-10-31") // output: "9/1/2020 – 10/31/2020"
 * @see https://moment.github.io/luxon/docs/manual/intl.html
 */
function formatDateRange(startIsoDate, endIsoDate) {
  const startDate = DateTime.fromISO(startIsoDate);
  const endDate = DateTime.fromISO(endIsoDate);
  let deliminator = "";

  const formattedStartDate = startDate.isValid
    ? startDate.toLocaleString()
    : "";
  const formattedEndDate = endDate.isValid ? endDate.toLocaleString() : "";

  if (formattedStartDate && formattedEndDate) {
    deliminator = " – ";
  }

  return `${formattedStartDate}${deliminator}${formattedEndDate}`;
}

export default formatDateRange;
