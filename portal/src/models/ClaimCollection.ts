import BaseCollection from "./BaseCollection";
import Claim from "./Claim";

export default class ClaimCollection extends BaseCollection<Claim> {
  get idProperty() {
    return "fineos_absence_id";
  }
}
