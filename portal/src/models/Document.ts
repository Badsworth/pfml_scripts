/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Document (AKA File) model and enum values
 */
import LeaveReason, { LeaveReasonType } from "./LeaveReason";
import { ValuesOf } from "../../types/common";

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

export const OtherDocumentType = {
  appealAcknowledgment: "Appeal Acknowledgment",
  approvalNotice: "Approval Notice",
  approvedTimeCancelled: "Approved Time Cancelled",
  benefitAmountChangeNotice: "Benefit Amount Change Notice",
  changeRequestApproved: "Change Request Approved",
  changeRequestDenied: "Change Request Denied",
  denialNotice: "Denial Notice",
  identityVerification: "Identification Proof",
  leaveAllotmentChangeNotice: "Leave Allotment Change Notice",
  maximumWeeklyBenefitChangeNotice: "Maximum Weekly Benefit Change Notice",
  medicalCertification: "State managed Paid Leave Confirmation",
  requestForInfoNotice: "Request for more Information",
  withdrawalNotice: "Pending Application Withdrawn",
} as const;

export type DocumentTypeEnum =
  | ValuesOf<typeof CertificationType>
  | ValuesOf<typeof OtherDocumentType>;

/**
 * Enums for Document `document_type` field.  In the `certification` object, `certificationForm` is only used for uploads of certification forms; the API then sets the plan
 * proof based on leave reason.  The other `certification` types are used when we retrieve documents from FINEOS.
 * @enum {string}
 */
export const DocumentType = {
  certification: { ...CertificationType },
  ...OtherDocumentType,
} as const;

/**
 * A document record from the application endpoints
 */
export interface BenefitsApplicationDocument {
  content_type: string;
  created_at: string;
  description: string;
  document_type: DocumentTypeEnum;
  fineos_document_id: string;
  name: string;
  user_id: string;
  application_id: string;
}

/**
 * A document record from the employer endpoints
 */
export interface ClaimDocument {
  content_type: string;
  created_at: string;
  description: string | null;
  document_type: DocumentTypeEnum;
  fineos_document_id: string;
  name: string | null;
}

/**
 * Get only documents associated with a given Application
 */
export function filterByApplication(
  items: Array<BenefitsApplicationDocument | ClaimDocument>,
  application_id: string
) {
  return items.filter((item) => {
    return (
      isBenefitsApplicationDocument(item) &&
      item.application_id === application_id
    );
  });
}

/**
 * Get certification documents based on application leave reason
 */
export function findDocumentsByLeaveReason<
  T extends BenefitsApplicationDocument | ClaimDocument
>(documents: T[], leaveReason?: LeaveReasonType): T[] {
  // TODO (CP-2029): Remove the medicalCertification type from this array when it becomes obsolete
  const documentFilters: Array<
    typeof DocumentType.certification[keyof typeof DocumentType.certification]
  > = [DocumentType.certification.medicalCertification];

  if (leaveReason) {
    documentFilters.push(DocumentType.certification[leaveReason]);
  }
  return findDocumentsByTypes(documents, documentFilters);
}

/**
 * Get only documents associated with a given selection of document_types
 */
export function findDocumentsByTypes<
  T extends BenefitsApplicationDocument | ClaimDocument
>(documents: T[], document_types: DocumentTypeEnum[]): T[] {
  const lowerCaseDocumentTypes = document_types.map((documentType) =>
    documentType.toLowerCase()
  );

  return documents.filter((document) => {
    // Ignore casing differences by comparing lowercased enums
    return lowerCaseDocumentTypes.includes(
      document.document_type.toLowerCase()
    );
  });
}

/**
 * Get only documents that are legal notices.
 */
export function getLegalNotices(
  documents: Array<BenefitsApplicationDocument | ClaimDocument>
) {
  return findDocumentsByTypes(documents, [
    DocumentType.appealAcknowledgment,
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
    DocumentType.maximumWeeklyBenefitChangeNotice,
    DocumentType.benefitAmountChangeNotice,
    DocumentType.leaveAllotmentChangeNotice,
    DocumentType.approvedTimeCancelled,
    DocumentType.changeRequestApproved,
    DocumentType.changeRequestDenied,
  ]);
}

export function isBenefitsApplicationDocument(
  document: BenefitsApplicationDocument | ClaimDocument
): document is BenefitsApplicationDocument {
  return "application_id" in document;
}

export function isClaimDocument(
  document: BenefitsApplicationDocument | ClaimDocument
): document is ClaimDocument {
  return !isBenefitsApplicationDocument(document);
}
