import { uniqueId } from "lodash";

/**
 * Model for managing temporary Files before they are successfully uploaded
 */
class TempFile {
  id?: string = uniqueId("TempFile");
  file: Blob;

  constructor(attrs: TempFile) {
    Object.assign(this, attrs);
  }
}

export default TempFile;
