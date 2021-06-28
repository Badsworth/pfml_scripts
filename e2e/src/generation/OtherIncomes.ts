import { OtherIncome } from "../api";
import { getLeavePeriod } from "../util/claims";
import { ApplicationLeaveDetails } from "../_api";

/**
 * Generates other incomes for the claim. Prefills start & end dates to be the same as leave dates.
 * @param spec - Claim specification, if has other_incomes listed.
 */
export function generateOtherIncomes(
  other_incomes: OtherIncome[] | undefined,
  leave_details: ApplicationLeaveDetails
): OtherIncome[] | undefined {
  if (!other_incomes || !other_incomes.length) return;
  const [startDate, endDate] = getLeavePeriod(leave_details);
  return other_incomes?.map((income) => {
    // only set start and end dates if they weren't specified
    if (income.income_start_date && income.income_end_date) return income;
    return {
      ...income,
      income_start_date: startDate,
      income_end_date: endDate,
    };
  });
}
