/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Concurrent leave
 */
import BaseModel from "./BaseModel";

class ConcurrentLeave extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'ConcurrentLeave' is n... Remove this comment to see the full error message
  get defaults() {
    return {
      is_for_current_employer: null,
      leave_end_date: null,
      leave_start_date: null,
    };
  }
}

export default ConcurrentLeave;
