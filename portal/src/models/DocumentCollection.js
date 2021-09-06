import Document, { DocumentType } from "./Document";
import BaseCollection from "./BaseCollection";
import findDocumentsByTypes from "../utils/findDocumentsByTypes";

export default class DocumentCollection extends BaseCollection {
  get idProperty() {
    return "fineos_document_id";
  }

  /**
   * Get only documents associated with a given Application
   * @param {string} application_id - ID of the target Application
   * @returns {Document[]}
   */
  filterByApplication(application_id) {
    return this.items.filter((item) => item.application_id === application_id);
  }

  /**
   * Gets legal notices from the current collection.
   * @returns {Document[]}
   */
  get legalNotices() {
    return findDocumentsByTypes(this.items, [
      DocumentType.approvalNotice,
      DocumentType.denialNotice,
      DocumentType.requestForInfoNotice,
    ]).map((documentAttrs) => new Document({ ...documentAttrs }));
  }
}
