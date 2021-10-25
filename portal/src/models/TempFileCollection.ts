import BaseCollection from "./BaseCollection";
import TempFile from "./TempFile";

export default class TempFileCollection extends BaseCollection<TempFile> {
  get idProperty() {
    return "id";
  }
}
