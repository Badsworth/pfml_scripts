import BaseCollection from "./BaseCollection";
import BenefitsApplication from "./BenefitsApplication";

export default class BenefitsApplicationCollection extends BaseCollection<BenefitsApplication> {
  get idProperty() {
    return "application_id";
  }
}
