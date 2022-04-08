import { merge } from "lodash";

export class ChangeRequest {
  change_request_id: string;
  fineos_abence_id: string;
  change_request_type: string | null;
  start_date: string | null;
  end_date: string | null;
  submitted_time: string | null;

  constructor(attrs: Partial<ChangeRequest>) {
    merge(this, attrs);
  }
}
