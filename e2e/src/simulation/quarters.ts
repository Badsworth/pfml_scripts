import { endOfQuarter, subQuarters } from "date-fns";

export function formatISODate(date: Date): string {
  return date.toISOString().split("T")[0].replace(/-/g, "");
}
export function formatISODatetime(date: Date): string {
  const dt = formatISODate(date);
  const hr = date.toISOString().split("T")[1].replace(/:/g, "").split(".")[0];
  return dt + hr;
}

const now = new Date();

// Return the end of the last N quarters from a reference date.
export default function quarters(refDate = now, number = 4): Date[] {
  const quarters = [];
  for (let i = number; i > 0; i--) {
    quarters.push(endOfQuarter(subQuarters(refDate, i)));
  }
  return quarters;
}
