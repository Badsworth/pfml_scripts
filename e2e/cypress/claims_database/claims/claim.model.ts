import { model } from "mongoose";
import { IClaimDocument } from "./claim.types";
import ClaimSchema from "./claim.scehma";
export const UserModel = model<IClaimDocument>("claim", ClaimSchema);
