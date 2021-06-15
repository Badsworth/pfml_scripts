/** @typedef {import('../models/LeaveReason').default} LeaveReason */
/** @typedef {import('../models/Document').default} Document */

import { DocumentType } from "../../src/models/Document";
import LeaveReason from "../../src/models/LeaveReason";
import findDocumentsByTypes from "./findDocumentsByTypes";
import { isFeatureEnabled } from "../services/featureFlags";

/**
 * Get certification documents based on application leave reason
 * @param {Document[]} documents
 * @param {LeaveReason} leaveReason
 * @returns {Document[]}
 */
const findDocumentsByLeaveReason = (
  documents,
  leaveReason,
  pregnant_or_recent_birth = false
) => {
  // TODO (CP-2029): Remove the medicalCertification type from this array when it becomes obsolete
  const documentFilters = [DocumentType.certification.medicalCertification];

  // TODO (CP-1983): Remove caring leave feature flag check
  // TODO (CP-2306): Remove or disable useNewPlanProofs feature flag to coincide with FINEOS 6/25 udpate
  const useNewPlanProofs = isFeatureEnabled("useNewPlanProofs");
  if (useNewPlanProofs) {
    // TODO (CP-2238): Remove check for pregnant_or_recent_birth
    if (pregnant_or_recent_birth) {
      documentFilters.push(DocumentType.certification[LeaveReason.pregnancy]);
    } else if (leaveReason) {
      documentFilters.push(DocumentType.certification[leaveReason]);
    }
  }

  return findDocumentsByTypes(documents, documentFilters);
};

export default findDocumentsByLeaveReason;
