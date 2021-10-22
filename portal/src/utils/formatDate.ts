import { DateTime } from "luxon";

/**
 * Format the given date as an internationalized, human-readable string
 */
export default function formatDate(isoDate: string) {
  const dateTime = DateTime.fromISO(isoDate);

  return {
    full: () => {
      if (dateTime.isValid) {
        return dateTime.toLocaleString(DateTime.DATE_FULL);
      }

      return "";
    },

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
