import { DocumentTypeEnum } from "./Document";

/**
 * A document record from the application endpoints
 */
class BenefitsApplicationDocument {
  content_type: string | null;
  created_at: string | null;
  description: string;
  document_type: DocumentTypeEnum | null;
  fineos_document_id: string | null;
  name: string;
  user_id: string;
  application_id: string;

  constructor(attrs: BenefitsApplicationDocument) {
    Object.assign(this, attrs);
  }
}

export default BenefitsApplicationDocument;
