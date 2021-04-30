/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Other income source
 */

import BaseModel from "./BaseModel";

export class Occupation extends BaseModel {
  get defaults() {
    return {
      occupation_code: null,
      occupation_description: null,
      occupation_id: null,
    };
  }
}

export class OccupationTitle extends BaseModel {
  get defaults() {
    return {
      occupation_id: null,
      occupation_title_code: null,
      occupation_title_description: null,
      occupation_title_id: null,
    };
  }
}
