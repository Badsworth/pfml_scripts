/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Employer Claim model
 */
import BaseClaim from "./BaseClaim";
import { merge } from "lodash";

class EmployerClaim extends BaseClaim {
  get defaults() {
    return merge({
      ...super.defaults,
      follow_up_date: null,
    });
  }
}

/**
 * TODO (EMPLOYER-601): Will remove after CPS & BE update enum values for leave reason
 * Enums for the Application's `leave_details.reason` field as provided by FINEOS
 * @enum {string}
 */
export const FineosLeaveReason = {
  activeDutyFamily: "Military Exigency Family",
  bonding: "Child Bonding",
  care: "Care of Family Member",
  medical: "Serious Health Condition",
  pregnancy: "Pregnancy/Maternity",
  serviceMemberFamily: "Military Caregiver",
};

/**
 * TODO (EMPLOYER-601): Will remove after CPS & BE update enum values for employer benefit type
 * Enums for the EmployerBenefit `benefit_type` field as provided by FINEOS
 * @enum {string}
 */
export const FineosEmployerBenefitType = {
  familyOrMedicalLeave: "Family or medical leave insurance",
  paidLeave: "Accrued paid leave",
  permanentDisability: "Permanent disability insurance",
  shortTermDisability: "Short-term disability insurance",
};

export default EmployerClaim;
