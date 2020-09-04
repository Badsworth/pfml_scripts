import { endOfQuarter, subQuarters } from "date-fns";

const now = new Date();

// Return the end of the last N quarters from a reference date.
export default function quarters(refDate = now, number = 4): Date[] {
  const quarters = [];
  for (let i = number; i > 0; i--) {
    quarters.push(endOfQuarter(subQuarters(refDate, i)));
  }
  return quarters;
}
