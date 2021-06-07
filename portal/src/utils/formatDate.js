import { DateTime } from "luxon";

/**
 * Format the given date as an internationalized, human-readable string
 * @param {string} isoDate - ISO 8601 date string
 * @returns {{ full: Function, short: Function }}
 */
export default function formatDate(isoDate) {
  const dateTime = DateTime.fromISO(isoDate);

  return {
    /**
     * @returns {string} date formatted as January 1, 2000
     */
    full: () => {
      if (dateTime.isValid) {
        return dateTime.toLocaleString(DateTime.DATE_FULL);
      }

      return "";
    },
    /**
     * @returns {string} date formatted as 1/1/2000
     */
    short: () => {
      if (dateTime.isValid) {
        return dateTime.toLocaleString();
      }

      // Support masked dates, which wouldn't be considered valid above
      if (isoDate && isoDate.includes("*")) {
        const [year, month, day] = isoDate
          .split("-")
          // Remove leading zeros
          .map((datePart) => datePart.replace(/^0/, ""));
        return `${month}/${day}/${year}`;
      }

      return "";
    },
  };
}
