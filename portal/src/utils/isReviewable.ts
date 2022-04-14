import { AbsencePeriod, finalDecisions } from "../models/AbsencePeriod";
import {
  ManagedRequirement,
  getSoonestReviewableManagedRequirement,
} from "../models/ManagedRequirement";

/**
 * Utility to determine whether a claim is reviewable.
 *
 * Created to share logic across Claim and EmployerClaim models until
 * such time those can be combined (PORTAL-477 pending)
 * or the logic moved to the backend.
 */
export const isReviewable = (
  absencePeriods: AbsencePeriod[],
  managedRequirements: ManagedRequirement[]
) => {
  const hasUnresolvedAbsencePeriods = absencePeriods.some((absence_period) => {
    return !finalDecisions.includes(absence_period.request_decision);
  });

  return (
    !!getSoonestReviewableManagedRequirement(managedRequirements) &&
    hasUnresolvedAbsencePeriods
  );
};
