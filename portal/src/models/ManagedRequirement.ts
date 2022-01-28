import { compact } from "lodash";
import dayjs from "dayjs";
import formatDate from "../utils/formatDate";

/**
 * Managed requirements primarily track the status of a claim's info request process.
 * Also referred to as an "Outstanding Requirement" in the FINEOS interface.
 */
export interface ManagedRequirement {
  category: string;
  created_at: string;
  follow_up_date: string | null;
  responded_at: string | null;
  status: "Open" | "Complete" | "Suppressed";
  type: string;
}

/**
 * @returns Follow-up date of the "soonest due" managed requirement.
 * Formatted for display to the user if `formattedDate` is `true`.
 */
export function getClosestReviewableFollowUpDate(
  managedRequirements: ManagedRequirement[],
  formattedDate = true
): string | undefined {
  const today = dayjs().format("YYYY-MM-DD");
  const followUpDates = compact(
    managedRequirements.map((managedRequirement) => {
      if (
        managedRequirement.status === "Open" &&
        managedRequirement.follow_up_date &&
        managedRequirement.follow_up_date >= today
      ) {
        return managedRequirement.follow_up_date;
      }
      return undefined;
    })
  );

  if (followUpDates.length === 0) return;
  const followUpDate = followUpDates.sort()[0];

  if (formattedDate) {
    return formatDate(followUpDate).short();
  }
  return followUpDate;
}

export default getClosestReviewableFollowUpDate;
