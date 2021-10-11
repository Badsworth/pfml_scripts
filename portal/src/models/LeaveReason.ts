/**
 * Enums for an absence case's `leave_details.reason` field. Claimant Portal sends some of these,
 * and Leave Admin portal needs to display any that a claimant can apply to via any channel.
 * @enum {string}
 */
const LeaveReason = {
  // TODO (CP-534): Confirm this enum value once integrated with the API
  activeDutyFamily: "Military Exigency Family",
  bonding: "Child Bonding",
  care: "Care for a Family Member",
  medical: "Serious Health Condition - Employee",
  // TODO (CP-1164): Send this option to the API when user indicates they're pregnant
  pregnancy: "Pregnancy/Maternity",
  // TODO (CP-534): Confirm this enum value once integrated with the API
  serviceMemberFamily: "Military Caregiver",
};

export default LeaveReason;
