import BaseCollection from "./BaseCollection";

export default class ClaimCollection extends BaseCollection {
  get idProperty() {
    return "application_id";
  }
}
