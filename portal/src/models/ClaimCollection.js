import BaseCollection from "./BaseCollection";

export default class ClaimCollection extends BaseCollection {
  get idProperty() {
    return "fineos_absence_id";
  }
}
