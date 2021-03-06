import formatDate from "./formatDate";
import { t } from "../locales/i18n";

/**
 * Format the given dates and display them as a range. Dates are
 * formatted using the user's default locale, which produces
 * internationalized, human-readable strings.
 * @example formatDateRange("2020-09-01", "2020-10-31") // output: "9/1/2020 to 10/31/2020"
 * @example formatDateRange("2020-09-01", "2020-10-31", "–") // output: "9/1/2020 – 10/31/2020"
 * @example formatDateRange("2020-09-01") // output: "9/1/2020"
 */
export default function formatDateRange(
  startIsoDate: string | null,
  endIsoDate?: string | null,
  customDelimiter?: string
) {
  const startDate = startIsoDate ? formatDate(startIsoDate).short() : "";
  const endDate = endIsoDate ? formatDate(endIsoDate).short() : "";

  let delimiter = "";

  if (startDate && endDate) {
    // Set the default delimiter from the i18n file
    delimiter = ` ${t("shared.dateRangeDelimiter")} `;

    // Use a custom delimiter if one is passed
    if (customDelimiter !== undefined) {
      delimiter = ` ${customDelimiter} `;
    }
  }

  return `${startDate}${delimiter}${endDate}`;
}
