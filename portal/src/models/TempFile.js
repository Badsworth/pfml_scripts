import BaseModel from "./BaseModel";
import { uniqueId } from "lodash";

/**
 * Model for managing temporary Files before they are successfully
 * uploaded
 */
class TempFile extends BaseModel {
  get defaults() {
    return {
      id: uniqueId("TempFile"),
      file: null,
    };
  }
}

export default TempFile;
