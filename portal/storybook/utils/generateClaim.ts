import { MockBenefitsApplicationBuilder } from "tests/test-utils";

/**
 * Generates claim of type (e.g., completed)
 * @param {string} type - completed, employed, address, submitted, etc..
 * @param {string} leaveReason - bonding, caring, medical, or pregnancy.
 * @returns {MockBenefitsApplicationBuilder}
 */
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'type' implicitly has an 'any' type.
export const generateClaim = (type, leaveReason) => {
  // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  const claim = new MockBenefitsApplicationBuilder()[type]();
  if (leaveReason) {
    const claimLeaveReason = `${leaveReason}LeaveReason`;
    claim[claimLeaveReason]();
  }

  return claim.create();
};
