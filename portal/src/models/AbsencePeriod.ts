import { LeaveReasonType } from "./LeaveReason";

export type AbsencePeriodRequestDecision =
  | "Approved"
  | "Cancelled"
  | "Denied"
  | "In Review"
  | "Pending"
  // Projected is (at least) used for Bonding Leave periods created automatically
  // for periods with Birth Disability as the reason qualifier
  | "Projected"
  | "Voided"
  | "Withdrawn";

export class AbsencePeriod {
  absence_period_end_date: string;
  absence_period_start_date: string;
  fineos_leave_request_id: string | null = null;
  period_type: "Continuous" | "Intermittent" | "Reduced Schedule";
  reason: LeaveReasonType;
  reason_qualifier_one = "";
  reason_qualifier_two = "";
  request_decision: AbsencePeriodRequestDecision;

  constructor(attrs: Partial<AbsencePeriod> = {}) {
    Object.assign(this, attrs);
  }
}
