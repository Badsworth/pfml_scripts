import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../src/models/Document";

export const createMockBenefitsApplicationDocument = (
  customAttrs: Partial<BenefitsApplicationDocument> = {}
): BenefitsApplicationDocument => ({
  application_id: "mock_application_id",
  content_type: "application/pdf",
  created_at: "2020-01-01T00:00:00.000Z",
  description: "",
  document_type:
    DocumentType.certification["Serious Health Condition - Employee"],
  fineos_document_id: "mock_document_id",
  name: "mock_document_name",
  user_id: "mock_user_id",
  ...customAttrs,
});
