import { LeaveReason } from "../types";
import { DocumentUploadRequest } from "../api";

export function getCertificationDocumentType(
  reason: LeaveReason
): DocumentUploadRequest["document_type"] {
  // After the SP, document types are renamed.
  switch (reason) {
    case "Child Bonding":
      return "Child bonding evidence form";
    case "Serious Health Condition - Employee":
      return "Own serious health condition form";
    case "Care for a Family Member":
      return "Care for a family member form";
    default:
      throw new Error(
        `Unable to determine name of certification doc for leave reason "${reason}"`
      );
  }
}

export function getDocumentReviewTaskName(
  documentType: DocumentUploadRequest["document_type"]
): string {
  switch (documentType) {
    case "Child bonding evidence form":
      return "Bonding Certification Review";
    case "Own serious health condition form":
      return "Medical Certification Review";
    case "Identification Proof":
      return "ID Review";
    case "State managed Paid Leave Confirmation":
      return "Certification Review";
    case "Care for a family member form":
      return "Caring Certification Review";
    case "Pregnancy/Maternity form":
      return "Medical Pregnancy Certification Review";
    default:
      throw new Error(
        `Unable to determine document review task for "${documentType}"`
      );
  }
}

export function findCertificationDoc<
  T extends Pick<DocumentUploadRequest, "document_type">
>(documents: T[]): T {
  const certificationDoc = documents.find(
    (doc) => doc.document_type !== "Identification Proof"
  );
  if (!certificationDoc) {
    throw new Error("No certification document was found");
  }
  return certificationDoc;
}
