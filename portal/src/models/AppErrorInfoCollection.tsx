import AppErrorInfo from "./AppErrorInfo";
import BaseCollection from "./BaseCollection";

export default class AppErrorInfoCollection extends BaseCollection<AppErrorInfo> {
  get idProperty() {
    return "key";
  }
}
