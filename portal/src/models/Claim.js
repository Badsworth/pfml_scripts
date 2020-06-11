/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class Claim extends BaseModel {
  get defaults() {
    return {
      application_id: null,
      // TODO: We'll map this to the correct API field once we get into Intermittent Leave work
      avg_weekly_hours_worked: null,
      created_at: null,
      duration_type: null,
      employee_ssn: null,
      first_name: null,
      // TODO: We'll map this to the correct API field once we get into Intermittent Leave work
      hours_off_needed: null,
      last_name: null,
      leave_details: {
        continuous_leave_periods: null,
        employer_notified: null,
        reason: null,
      },
      middle_name: null,
    };
  }
}

export default Claim;
