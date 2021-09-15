/** @typedef {import('../models/LeaveReason').default} LeaveReason */
/** @typedef {import('../models/Document').default} Document */

import { DocumentType } from "../../src/models/Document";
import findDocumentsByTypes from "./findDocumentsByTypes";

/**
 * Get certification documents based on application leave reason
 * @param {Document[]} documents
 * @param {LeaveReason} leaveReason
 * @returns {Document[]}
 */
const findDocumentsByLeaveReason = (documents, leaveReason) => {
  // TODO (CP-2029): Remove the medicalCertification type from this array when it becomes obsolete
  const documentFilters = [DocumentType.certification.medicalCertification];

  if (leaveReason) {
    documentFilters.push(DocumentType.certification[leaveReason]);
  }
  return findDocumentsByTypes(documents, documentFilters);
};

export default findDocumentsByLeaveReason;
