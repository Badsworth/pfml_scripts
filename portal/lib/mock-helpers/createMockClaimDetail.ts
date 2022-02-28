import {
  AbsencePeriod,
  AbsencePeriodRequestDecisionEnum,
  AbsencePeriodTypes,
} from "src/models/AbsencePeriod";
import ClaimDetail from "src/models/ClaimDetail";

import { ClaimEmployee } from "src/models/Claim";
import LeaveReason from "src/models/LeaveReason";
import { ReasonQualifier } from "src/models/BenefitsApplication";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";
import { faker } from "@faker-js/faker";

export const leaveScenarioMap: {
  [scenario: string]: Array<Partial<AbsencePeriod>>;
} = {
  "Bonding (adoption)": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.adoption,
    },
  ],
  "Bonding (foster)": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.fosterCare,
    },
  ],
  "Bonding (newborn)": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.newBorn,
    },
  ],
  "Caring leave": [{ reason: LeaveReason.care }],
  "Medical (illness)": [{ reason: LeaveReason.medical }],
  "Medical (pregnancy)": [{ reason: LeaveReason.pregnancy }],
  "Medical (pregnancy and bonding)": [
    { reason: LeaveReason.pregnancy },
    { reason: LeaveReason.bonding, reason_qualifier_one: "Newborn" },
  ],
};

export const leaveTypes: AbsencePeriodTypes[] = [
  "Continuous",
  "Intermittent",
  "Reduced Schedule",
];

export const requestTypes: AbsencePeriodRequestDecisionEnum[] = [
  "Approved",
  "Cancelled",
  "Denied",
  "In Review",
  "Pending",
  "Projected",
  "Withdrawn",
];

/**
 * Creates mock claim details
 * @returns {ClaimDetail}
 *
 * @example
 * createMockClaimDetail({
 *   leaveScenario: "Bonding (adoption)",
 *   leaveType: "Continuous",
 *   requestDecision: "Approved",
 * });
 */
const createMockClaimDetail = ({
  absencePeriods,
  hasPaidPayments,
  leaveScenario = "Bonding (adoption)",
  leaveType = "Continuous",
  requestDecision = "Approved",
}: {
  absencePeriods?: AbsencePeriod[];
  hasPaidPayments?: boolean;
  leaveScenario?: keyof typeof leaveScenarioMap;
  leaveType?: AbsencePeriodTypes;
  requestDecision?: AbsencePeriodRequestDecisionEnum;
}): ClaimDetail => {
  const reasonDetails = leaveScenarioMap[leaveScenario];
  const defaultAbsencePeriods = reasonDetails.map((reasonDetail) => {
    return createAbsencePeriod({
      ...reasonDetail,
      period_type: leaveType,
      request_decision: requestDecision,
    });
  });

  return new ClaimDetail({
    absence_periods: absencePeriods || defaultAbsencePeriods,
    application_id: "mock-application-id",
    employee: new ClaimEmployee({
      first_name: faker.name.firstName(),
      last_name: faker.name.lastName(),
    }),
    employer: {
      employer_dba: faker.company.companyName(),
      employer_fein: "123456789",
      employer_id: faker.datatype.uuid(),
    },
    fineos_absence_id: "NTN-12345-ABS-01",
    fineos_notification_id: faker.datatype.uuid(),
    has_paid_payments: hasPaidPayments,
    managed_requirements: [],
    outstanding_evidence: {
      employee_evidence: [],
      employer_evidence: [],
    },
  });
};

export default createMockClaimDetail;
