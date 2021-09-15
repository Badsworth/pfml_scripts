import BaseCollection from "./BaseCollection";

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
}
