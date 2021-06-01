import { DateTime } from "luxon";

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
function formatDateRange(startIsoDate, endIsoDate) {
  const startDate = formatDate(startIsoDate);
  const endDate = formatDate(endIsoDate);
  let deliminator = "";

  if (startDate && endDate) {
    deliminator = " – ";
  }

  return `${startDate}${deliminator}${endDate}`;
}

/**
 * Format the given date as an internationalized, human-readable string
 * @param {string} isoDate - ISO 8601 date string
 * @returns {string}
 */
export function formatDate(isoDate) {
  if (!isoDate) return "";

  const dateTime = DateTime.fromISO(isoDate);
  if (dateTime.isValid) {
    return dateTime.toLocaleString();
  }

  // Support masked dates, which wouldn't be considered valid above
  if (isoDate.includes("*")) {
    const [year, month, day] = isoDate
      .split("-")
      // Remove leading zeros
      .map((datePart) => datePart.replace(/^0/, ""));
    return `${month}/${day}/${year}`;
  }

  return "";
}

export default formatDateRange;
