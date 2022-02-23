import dayjs from "dayjs";

/**
 * Format the given date as an internationalized, human-readable string
 */
export default function formatDate(isoDate?: string | null) {
  return {
    full: () => {
      if (!isoDate) return "";
      const date = dayjs(isoDate);
      if (date.isValid()) {
        return new Intl.DateTimeFormat("default", {
          dateStyle: "long",
        }).format(date.toDate());
      }

      return "";
    },

    short: () => {
      if (!isoDate) return "";

      // Support masked dates, which wouldn't be considered valid above
      if (isoDate && isoDate.includes("*")) {
        const [year, month, day] = isoDate
          .split("-")
          // Remove leading zeros
          .map((datePart) => datePart.replace(/^0/, ""));
        return `${month}/${day}/${year}`;
      }

      const date = dayjs(isoDate);
      if (date.isValid()) {
        return new Intl.DateTimeFormat().format(date.toDate());
      }

      return "";
    },
  };
}
