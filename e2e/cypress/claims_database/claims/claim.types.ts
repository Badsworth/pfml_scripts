import { Document, Model } from "mongoose";
export interface IClaim {
  scenario: string;
  claimId: string;
  fineosAbsenceId: string;
  startDate: string;
  endDate: string;
  environment: string;
  clean: boolean;
}
export interface IClaimDocument extends IClaim, Document {}
export interface IClaimModel extends Model<IClaimDocument> {}
