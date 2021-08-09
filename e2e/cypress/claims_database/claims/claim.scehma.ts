import { Schema } from "mongoose";
const ClaimSchema = new Schema({
  scenario: String,
  claimId: String,
  fineosAbsenceId: String,
  startDate: String,
  endDate: String,
  environment: String, // optimizing for the quantity of claims submitted per environment is going to be tricky here - we might only run this in test to start with
  clean: Boolean,
});
export default ClaimSchema;
