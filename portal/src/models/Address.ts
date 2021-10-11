/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class Address extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'Address' is not assig... Remove this comment to see the full error message
  get defaults() {
    return {
      city: null,
      line_1: null,
      line_2: null,
      state: null,
      zip: null,
    };
  }
}

export default Address;
