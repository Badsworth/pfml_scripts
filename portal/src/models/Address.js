/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class Address extends BaseModel {
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
