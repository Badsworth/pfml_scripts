import BaseCollection from "./BaseCollection";

export default class AppErrorInfoCollection extends BaseCollection {
  get idProperty() {
    return "key";
  }
}
