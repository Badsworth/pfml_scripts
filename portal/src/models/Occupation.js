/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Other income source
 */

import BaseModel from "./BaseModel";

export default class Occupation extends BaseModel {
  get defaults() {
    return {
      occupation_code: null,
      occupation_description: null,
      occupation_id: null,
    };
  }
}
