import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import ClaimDocument from "../models/ClaimDocument";
import { DocumentType } from "../models/Document";
import findDocumentsByTypes from "./findDocumentsByTypes";

/**
 * Get certification documents based on application leave reason
 */
function findDocumentsByLeaveReason<
  T extends BenefitsApplicationDocument | ClaimDocument
>(documents: T[], leaveReason): T[] {
  // TODO (CP-2029): Remove the medicalCertification type from this array when it becomes obsolete
  const documentFilters = [DocumentType.certification.medicalCertification];

  if (leaveReason) {
    documentFilters.push(DocumentType.certification[leaveReason]);
  }
  return findDocumentsByTypes(documents, documentFilters);
}

export default findDocumentsByLeaveReason;
