import BaseCollection from "./BaseCollection";

export default class TempFileCollection extends BaseCollection {
  get idProperty() {
    return "id";
  }
}
