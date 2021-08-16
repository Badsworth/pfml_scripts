/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Concurrent leave
 */
import BaseModel from "./BaseModel";

class ConcurrentLeave extends BaseModel {
  get defaults() {
    return {
      is_for_current_employer: null,
      leave_end_date: null,
      leave_start_date: null,
    };
  }
}

export default ConcurrentLeave;
