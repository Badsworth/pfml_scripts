import { ValuesOf } from "../../types/common";
import { merge } from "lodash";

export const ChangeRequestType = {
  modification: "Modification",
  withdrawal: "Withdrawal",
  medicalToBonding: "Medical To Bonding Transition",
} as const;

export default class ChangeRequest {
  change_request_id: string;
  fineos_absence_id: string;
  change_request_type: ValuesOf<typeof ChangeRequestType> | null = null;
  start_date: string | null = null;
  end_date: string | null = null;
  submitted_time: string | null = null;

  constructor(attrs: Partial<ChangeRequest>) {
    merge(this, attrs);
  }
}
