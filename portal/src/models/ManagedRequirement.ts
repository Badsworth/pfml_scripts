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
 * @returns Follow-up date of the "latest due" managed requirement, regardless of status.
 */
export function getLatestFollowUpDate(
  managedRequirements: ManagedRequirement[]
): string | null {
  const followUpDates = managedRequirements
    .map((managedRequirement) => managedRequirement.follow_up_date)
    .sort()
    .reverse();

  if (followUpDates.length === 0) return null;
  return followUpDates[0];
}

/**
 * @returns The "soonest due" Open managed requirement.
 */
export function getSoonestReviewableManagedRequirement(
  managedRequirements: ManagedRequirement[]
): ManagedRequirement | null {
  const today = dayjs().format("YYYY-MM-DD");
  const reviewableManagedRequirements = managedRequirements
    .filter(
      (managedRequirement) =>
        managedRequirement.status === "Open" &&
        managedRequirement.follow_up_date &&
        managedRequirement.follow_up_date >= today
    )
    .sort((a, b) => dayjs(a.follow_up_date).diff(dayjs(b.follow_up_date)));

  if (reviewableManagedRequirements.length === 0) return null;
  return reviewableManagedRequirements[0];
}

/**
 * @returns Follow-up date of the "soonest due" managed requirement.
 * Formatted for display to the user if `formattedDate` is `true`.
 */
export function getSoonestReviewableFollowUpDate(
  managedRequirements: ManagedRequirement[],
  formattedDate = true
): string | null {
  const closestReviewableManagedRequirement =
    getSoonestReviewableManagedRequirement(managedRequirements);

  if (!closestReviewableManagedRequirement) return null;
  const followUpDate = closestReviewableManagedRequirement.follow_up_date;

  if (formattedDate) {
    return formatDate(followUpDate).short();
  }
  return followUpDate;
}
