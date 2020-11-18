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

export default EmployerClaim;
