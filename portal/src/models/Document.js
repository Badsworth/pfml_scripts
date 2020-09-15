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
      document_category: null,
      document_id: null,
      document_type: null,
      fineos_id: null,
      name: null,
      size_bytes: null,
      updated_at: null,
      user_id: null,
    };
  }
}

export default Document;
