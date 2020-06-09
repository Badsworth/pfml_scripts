import BaseModel from "./BaseModel";

class Claim extends BaseModel {
  get defaults() {
    return {
      first_name: null,
      middle_name: null,
      last_name: null,
      application_id: null,
      created_at: null,
      avg_weekly_hours_worked: null,
      leave_details: {
        employer_notified: null,
      },
      // TODO: Move these into the nested format the API expects
      // https://lwd.atlassian.net/browse/CP-480
      duration_type: null,
      hours_off_needed: null,
      leave_type: null,
      leave_start_date: null,
      leave_end_date: null,
    };
  }
}

export default Claim;
