import { Document, Model } from "mongoose";
export interface IClaim {
  scenario: string;
  startDate: string;
  endDate: string;
  clean: boolean;
  claimId: string;
  fineosAbsenceId: string;
}
export interface IClaimDocument extends IClaim, Document {}
export interface IClaimModel extends Model<IClaimDocument> {}
