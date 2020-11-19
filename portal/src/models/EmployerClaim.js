/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Employer Claim model
 */
import BaseClaim from "./BaseClaim";

class EmployerClaim extends BaseClaim {}

/**
 * TODO (EMPLOYER-580): Will remove after reconciling difference in enum values for leave reason
 * Enums for the Application's `leave_details.reason` field as provided by FINEOS
 * @enum {string}
 */
export const FineosLeaveReason = {
  activeDutyFamily: "Military Exigency Family",
  bonding: "Child Bonding",
  care: "Care of Family Member",
  medical: "Serious Health Condition - Employee",
  pregnancy: "Pregnancy/Maternity",
  serviceMemberFamily: "Military Caregiver",
};

/**
 * TODO (EMPLOYER-580): Will remove after reconciling difference in enum values for employer benefit type
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
