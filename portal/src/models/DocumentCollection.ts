import { BenefitsApplicationDocument, ClaimDocument } from "./Document";
import BaseCollection from "./BaseCollection";

export default class DocumentCollection extends BaseCollection<
  BenefitsApplicationDocument | ClaimDocument
> {
  get idProperty() {
    return "fineos_document_id";
  }
}
