/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Previous leave period
 */
import BaseModel from "./BaseModel";

class PreviousLeave extends BaseModel {
  get defaults() {
    return {
      leave_end_date: null,
      leave_start_date: null,
    };
  }
}

export default PreviousLeave;
