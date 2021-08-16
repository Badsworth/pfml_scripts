import BaseModel from "./BaseModel";
import { uniqueId } from "lodash";

/**
 * Model for managing temporary Files before they are successfully
 * uploaded
 */
class TempFile extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'TempFile' is not assi... Remove this comment to see the full error message
  get defaults() {
    return {
      id: uniqueId("TempFile"),
      file: null,
    };
  }
}

export default TempFile;
