import BaseCollection from "./BaseCollection";

export default class DocumentCollection extends BaseCollection {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'idProperty' in type 'DocumentCollection'... Remove this comment to see the full error message
  get idProperty() {
    return "fineos_document_id";
  }

  /**
   * Get only documents associated with a given Application
   * @param {string} application_id - ID of the target Application
   * @returns {Document[]}
   */
  filterByApplication(application_id) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'DocumentC... Remove this comment to see the full error message
    return this.items.filter((item) => item.application_id === application_id);
  }
}
