import {
  BenefitsApplicationDocument,
  ClaimDocument,
  isBenefitsApplicationDocument,
} from "./Document";
import BaseCollection from "./BaseCollection";

export default class DocumentCollection extends BaseCollection<
  BenefitsApplicationDocument | ClaimDocument
> {
  get idProperty() {
    return "fineos_document_id";
  }

  /**
   * Get only documents associated with a given Application
   */
  filterByApplication(application_id: string) {
    return this.items.filter((item) => {
      return (
        isBenefitsApplicationDocument(item) &&
        item.application_id === application_id
      );
    });
  }
}
