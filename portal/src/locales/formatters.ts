/**
 * @file Defines custom i18n formatters which apply special formatting rules to specific
 * types of content strings. For example, currency values are formatted into a dollar amount
 * with dollar sign, a thousands separator comma, and cent values. Formatters can be internationalized
 * by using the locale value to change formatting behavior.
 * @see https://www.i18next.com/translation-function/formatting
 */
import convertMinutesToHours from "../utils/convertMinutesToHours";

/**
 * Add additional formatting to a given translation string
 * @see https://www.i18next.com/translation-function/formatting
 * @param {string} value - the string to be formatted
 * @param {string} format - the type of formatting
 * @param {string} locale - language code
 * @returns {string} formatted value
 */
export default function formatValue(value, format, locale) {
  if (format === "currency") {
    return formatCurrency(value, locale);
  } else if (format === "ein") {
    return formatEmployerFein(value);
  } else if (format === "hoursMinutesDuration") {
    return formatHoursMinutesDuration(value, locale);
  }
  return value;
}

/**
 * Formats number into currency. For example:
 *   1000 -> $1,000.00
 * @param {string} value - the string to be formatted
 * @param {string} locale - language code
 * @returns {string} formatted value
 */
function formatCurrency(value, locale) {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD",
  }).format(value);
}

/**
 * Formats an EIN returned from the server to utilize a non-breaking hyphen
 * so that the entire EIN is always displayed on the same line if possible.
 * @param {string} value - the string to be formatted
 * @returns {string} formatted value
 */
function formatEmployerFein(value) {
  return value.replace("-", "‑");
}

/**
 * Formats a duration into hours and minutes. For example:
 *   480 -> 8h
 *   475 -> 7h 55m
 * @param {string} value - the string to be formatted
 * @param {string} _locale - language code
 * @returns {string} formatted value
 */
function formatHoursMinutesDuration(value, _locale) {
  // Add any internationalizations here. For example:
  // if (locale === 'en-US') {
  //   return `${value} minutes`
  // }

  // The default return value will be the English-idiomatic "h" and "m" abbreviations for
  // hours and minutes
  const { hours, minutes } = convertMinutesToHours(value);
  if (minutes === 0) return `${hours}h`;
  return `${hours}h ${minutes}m`;
}
