import BaseModel from "./BaseModel";

class Claim extends BaseModel {
  get defaults() {
    return {
      claim_id: null,
      created_at: null,
      avg_weekly_hours_worked: null,
      duration_type: null,
      hours_off_needed: null,
      leave_type: null,
      leave_start_date: null,
      leave_end_date: null,
    };
  }
}

export default Claim;
