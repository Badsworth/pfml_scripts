import { Schema, model, Document } from "mongoose";
import { DBClaimMetadata } from "../../../src/types";

export interface ClaimDocument extends DBClaimMetadata, Document {}

export type G = DBClaimMetadata;

const schema = new Schema<ClaimDocument>({
  scenario: { type: String, required: true },
  claimId: { type: String, required: true },
  fineosAbsenceId: { type: String, required: true },
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  status: { type: String, required: true },
  environment: { type: String, required: true },
  submittedDate: { type: Date, required: true },
});

const ClaimModel = model<ClaimDocument>("Claim", schema);

export default ClaimModel;
