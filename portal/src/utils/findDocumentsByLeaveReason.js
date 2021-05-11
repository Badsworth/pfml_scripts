/** @typedef {import('../models/BenefitsApplication').default} BenefitsApplication */
/** @typedef {import('../models/Document').default} Document */

import { DocumentType } from "../../src/models/Document";
import findDocumentsByTypes from "./findDocumentsByTypes";
import { isFeatureEnabled } from "../services/featureFlags";

/**
 * Get certification documents based on application leave reason
 * @param {Document[]} documents
 * @param {BenefitsApplication} application
 * @returns {Document[]}
 */
const findDocumentsByLeaveReason = (documents, application) => {
  // TODO (CP-2029): Remove the medicalCertification type from this array when it becomes obsolete
  const documentFilters = [DocumentType.certification.medicalCertification];

  // TODO (CP-1983): Remove caring leave feature flag check
  const showCaringLeaveType = isFeatureEnabled("showCaringLeaveType");
  if (showCaringLeaveType) {
    if (application.leave_details && application.leave_details.reason) {
      documentFilters.push(
        DocumentType.certification[application.leave_details.reason]
      );
    }
  }

  return findDocumentsByTypes(documents, documentFilters);
};

export default findDocumentsByLeaveReason;
