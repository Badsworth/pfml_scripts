import { model } from "mongoose";
import { IClaimDocument } from "./claim.types";
import ClaimSchema from "./claim.scehma";
export const ClaimModel = model<IClaimDocument>("claim", ClaimSchema);
