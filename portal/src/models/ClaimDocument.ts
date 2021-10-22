import { DocumentTypeEnum } from "./Document";

/**
 * A document record from the employer endpoints
 */
class ClaimDocument {
  content_type: string | null;
  created_at: string | null;
  description: string | null;
  document_type: DocumentTypeEnum;
  fineos_document_id: string;
  name: string | null;

  constructor(attrs: ClaimDocument) {
    Object.assign(this, attrs);
  }
}

export default ClaimDocument;
