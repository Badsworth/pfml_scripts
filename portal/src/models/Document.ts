/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Document (AKA File) model and enum values
 */
import LeaveReason from "./LeaveReason";

const CertificationType = {
  certificationForm: "Certification Form",
  [LeaveReason.activeDutyFamily]: "Military exigency form",
  [LeaveReason.care]: "Care for a family member form",
  [LeaveReason.bonding]: "Child bonding evidence form",
  [LeaveReason.medical]: "Own serious health condition form",
  [LeaveReason.pregnancy]: "Pregnancy/Maternity form",
  [LeaveReason.serviceMemberFamily]: "Care for a family member form",
  medicalCertification: "State managed Paid Leave Confirmation", // TODO (CP-2029): Remove this legacy type once claims filed before 7/1/2021 are adjudicated
} as const;

const OtherDocumentType = {
  appealAcknowledgment: "Appeal Acknowledgment",
  approvalNotice: "Approval Notice",
  denialNotice: "Denial Notice",
  identityVerification: "Identification Proof",
  medicalCertification: "State managed Paid Leave Confirmation",
  requestForInfoNotice: "Request for more Information",
  withdrawalNotice: "Pending Application Withdrawn",
} as const;

export type DocumentTypeEnum =
  | typeof CertificationType[keyof typeof CertificationType]
  | typeof OtherDocumentType[keyof typeof OtherDocumentType];

/**
 * Enums for Document `document_type` field.  In the `certification` object, `certificationForm` is only used for uploads of certification forms; the API then sets the plan
 * proof based on leave reason.  The other `certification` types are used when we retrieve documents from FINEOS.
 * @enum {string}
 */
export const DocumentType = {
  certification: { ...CertificationType },
  ...OtherDocumentType,
} as const;
