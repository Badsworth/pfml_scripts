import Collection from "./Collection";

export default class ClaimCollection extends Collection {
  get idProperty() {
    return "application_id";
  }
}
