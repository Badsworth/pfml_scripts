import BaseModel from "./BaseModel";

class Claim extends BaseModel {
  get defaults() {
    return {
      claimId: null,
      createdAt: null,
      avgWeeklyHoursWorked: null,
      durationType: null,
      hoursOffNeeded: null,
    };
  }
}

export default Claim;
