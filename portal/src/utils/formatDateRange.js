import formatDate from "./formatDate";

/**
 * Format the given dates and display them as a range. Dates are
 * formatted using the user's default locale, which produces
 * internationalized, human-readable strings.
 * @param {string} startIsoDate - ISO 8601 date string
 * @param {string} [endIsoDate] - ISO 8601 date string
 * @returns {string}
 * @example formatDateRange("2020-09-01", "2020-10-31") // output: "9/1/2020 – 10/31/2020"
 * @example formatDateRange("2020-09-01") // output: "9/1/2020"
 * @see https://moment.github.io/luxon/docs/manual/intl.html
 */
export default function formatDateRange(startIsoDate, endIsoDate) {
  const startDate = formatDate(startIsoDate).short();
  const endDate = formatDate(endIsoDate).short();
  let deliminator = "";

  if (startDate && endDate) {
    deliminator = " – ";
  }

  return `${startDate}${deliminator}${endDate}`;
}
