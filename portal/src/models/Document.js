/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Document (AKA File) model and enum values
 */
import BaseModel from "./BaseModel";
import LeaveReason from "./LeaveReason";

class Document extends BaseModel {
  get defaults() {
    return {
      application_id: null,
      content_type: null,
      created_at: null,
      description: null,
      document_type: null,
      fineos_document_id: null,
      name: null,
      user_id: null,
    };
  }
}

/**
 * Enums for Document `document_type` field
 * @enum {string}
 */
export const DocumentType = {
  approvalNotice: "Approval Notice",
  certification: {
    [LeaveReason.care]: "Care for a family member form",
    [LeaveReason.bonding]: "Child bonding evidence form",
    [LeaveReason.medical]: "Own serious health condition form",
    [LeaveReason.pregnancy]: "Pregnancy/Maternity form",
    medicalCertification: "State managed Paid Leave Confirmation", // TODO (CP-2029): Remove this legacy type once claims filed before 7/1/2021 are adjudicated
  },
  denialNotice: "Denial Notice",
  identityVerification: "Identification Proof",
  medicalCertification: "State managed Paid Leave Confirmation",
  requestForInfoNotice: "Request for more Information",
};

export default Document;
