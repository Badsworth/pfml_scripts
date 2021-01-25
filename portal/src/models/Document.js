/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Document (AKA File) model and enum values
 */
import BaseModel from "./BaseModel";

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
  denialNotice: "Denial Notice",
  identityVerification: "Identification Proof",
  medicalCertification: "State managed Paid Leave Confirmation",
  requestForInfoNotice: "Request for more Information",
};

export default Document;
