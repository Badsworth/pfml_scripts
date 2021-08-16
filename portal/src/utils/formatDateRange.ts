import formatDate from "./formatDate";
import { t } from "../locales/i18n";

/**
 * Format the given dates and display them as a range. Dates are
 * formatted using the user's default locale, which produces
 * internationalized, human-readable strings.
 * @param {string} startIsoDate - ISO 8601 date string
 * @param {string} [endIsoDate] - ISO 8601 date string
 * @param {string} [customDelimiter] - overrides the default dateRangeDelimiter
 * @returns {string}
 * @example formatDateRange("2020-09-01", "2020-10-31") // output: "9/1/2020 to 10/31/2020"
 * @example formatDateRange("2020-09-01", "2020-10-31", "–") // output: "9/1/2020 – 10/31/2020"
 * @example formatDateRange("2020-09-01") // output: "9/1/2020"
 * @see https://moment.github.io/luxon/docs/manual/intl.html
 */
export default function formatDateRange(
  startIsoDate,
  endIsoDate,
  customDelimiter
) {
  const startDate = formatDate(startIsoDate).short();
  const endDate = formatDate(endIsoDate).short();

  let delimiter = "";

  if (startDate && endDate) {
    // Set the default delimiter from the i18n file
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
    delimiter = ` ${t("shared.dateRangeDelimiter")} `;

    // Use a custom delimiter if one is passed
    if (customDelimiter !== undefined) {
      delimiter = ` ${customDelimiter} `;
    }
  }

  return `${startDate}${delimiter}${endDate}`;
}
