import { EmployerBenefit } from "../api";
import { getLeavePeriod } from "../util/claims";
import { ApplicationLeaveDetails } from "../_api";
import { ClaimSpecification } from "./Claim";

/**
 * Generates employer benefits for the claim. Prefills start & end dates to be the same as leave dates.
 * @param spec - Claim specification, if has other_incomes listed.
 */
export function generateEmployerBenefits(
  { employer_benefits }: ClaimSpecification,
  leave_details: ApplicationLeaveDetails
): EmployerBenefit[] | undefined {
  if (!employer_benefits || !employer_benefits.length) return;

  const [startDate, endDate] = getLeavePeriod(leave_details);

  return employer_benefits.map((benefit) => {
    // only set start and end dates if they weren't specified
    if (benefit.benefit_start_date) return benefit;
    return {
      ...benefit,
      benefit_start_date: startDate,
      benefit_end_date: endDate,
    };
  });
}
