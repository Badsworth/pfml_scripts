import BaseCollection from "./BaseCollection";
import BenefitsApplicationDocument from "./BenefitsApplicationDocument";
import ClaimDocument from "./ClaimDocument";

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
      if (item instanceof BenefitsApplicationDocument) {
        return item.application_id === application_id;
      }
      return false;
    });
  }
}
