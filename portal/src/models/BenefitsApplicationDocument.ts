import { DocumentTypeEnum } from "./Document";

/**
 * A document record from the application endpoints
 */
class BenefitsApplicationDocument {
  content_type: string;
  created_at: string;
  description: string;
  document_type: DocumentTypeEnum;
  fineos_document_id: string;
  name: string;
  user_id: string;
  application_id: string;

  constructor(attrs: BenefitsApplicationDocument) {
    Object.assign(this, attrs);
  }
}

export default BenefitsApplicationDocument;
