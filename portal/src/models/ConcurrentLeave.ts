/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Concurrent leave
 */

class ConcurrentLeave {
  is_for_current_employer: boolean | null = null;
  leave_end_date: string | null = null;
  leave_start_date: string | null = null;

  constructor(attrs: Partial<ConcurrentLeave>) {
    Object.assign(this, attrs);
  }
}

export default ConcurrentLeave;
