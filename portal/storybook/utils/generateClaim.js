import { MockBenefitsApplicationBuilder } from "tests/test-utils";

/**
 * Generates claim of type (e.g., completed)
 * @param {string} type - completed, employed, address, submitted, etc..
 * @param {string} leaveReason - bonding, caring, medical, or pregnancy.
 * @returns {MockBenefitsApplicationBuilder}
 */
export const generateClaim = (type, leaveReason) => {
  const claim = new MockBenefitsApplicationBuilder()[type]();
  if (leaveReason) {
    const claimLeaveReason = `${leaveReason}LeaveReason`;
    claim[claimLeaveReason]();
  }

  return claim.create();
};
