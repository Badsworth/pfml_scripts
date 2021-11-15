import ClaimStateTracker from "../ClaimStateTracker";
import { GeneratedClaim } from "../../generation/Claim";
import { map } from "streaming-iterables";
import stringify from "csv-stringify";
import { promisify } from "util";
import { pipeline, Readable } from "stream";
import * as fs from "fs";
import { ApplicationRequestBody } from "../../_api";
import { getLeavePeriodFromLeaveDetails } from "../../util/claims";
import { LeavePeriods } from "../../types";
import { format } from "date-fns";

const pipelineP = promisify(pipeline);

export default class SubmittedClaimIndex {
  static async write(
    filename: string,
    claims: AsyncIterable<GeneratedClaim>,
    tracker: ClaimStateTracker
  ): Promise<void> {
    const extract = map(
      async (
        claim: GeneratedClaim
      ): Promise<Record<string, string | null | undefined>> => {
        const stateRecord = (await tracker.get(claim.id)) ?? {};
        const row: Record<string, string | null | undefined> = {
          scenario: claim.scenario,
          id: claim.id,
          ssn: claim.claim.tax_identifier,
          fein: claim.claim.employer_fein,
          ...stateRecord,
          leave_start: format(findLeaveStart(claim.claim), "P"),
          leave_end: format(findLeaveEnd(claim.claim), "P"),
          claim_type: findClaimType(claim.claim),
          leave_period_type: findLeavePeriodType(claim.claim),
        };
        return row;
      }
    );

    const formatter = stringify({
      header: true,
      columns: {
        scenario: "Scenario",
        id: "Claim ID",
        ssn: "SSN",
        fein: "FEIN",
        fineos_absence_id: "Fineos ID",
        error: "Error",
        time: "Submitted Timestamp",
        leave_period_type: "Period Type",
        leave_start: "Leave Start",
        leave_end: "Leave End",
        claim_type: "Claim Type",
      },
    });
    await pipelineP(
      Readable.from(extract(claims)),
      formatter,
      fs.createWriteStream(filename)
    );
  }
}

function findClaimType(claim: ApplicationRequestBody) {
  const qualifier = claim.leave_details?.reason_qualifier;
  const reason = claim.leave_details?.reason;
  return `${reason}${qualifier ? `(${qualifier})` : ""}`;
}

function findLeavePeriodType(claim: ApplicationRequestBody) {
  if (claim.has_continuous_leave_periods) {
    return "Continuous";
  }
  if (claim.has_reduced_schedule_leave_periods) {
    return "Reduced";
  }
  if (claim.has_intermittent_leave_periods) {
    return "Intermittent";
  }
}

function findLeaveStart(claim: ApplicationRequestBody) {
  const types: (keyof LeavePeriods)[] = [
    "continuous_leave_periods",
    "reduced_schedule_leave_periods",
    "intermittent_leave_periods",
  ];
  for (const type of types) {
    if (claim.leave_details && (claim.leave_details?.[type]?.length ?? 0) > 0) {
      return getLeavePeriodFromLeaveDetails(claim.leave_details, type)[0];
    }
  }
  throw new Error("Unable to extract a leave start date for this start date.");
}

function findLeaveEnd(claim: ApplicationRequestBody) {
  const types: (keyof LeavePeriods)[] = [
    "continuous_leave_periods",
    "reduced_schedule_leave_periods",
    "intermittent_leave_periods",
  ];
  for (const type of types) {
    if (claim.leave_details && (claim.leave_details?.[type]?.length ?? 0) > 0) {
      return getLeavePeriodFromLeaveDetails(claim.leave_details, type)[1];
    }
  }
  throw new Error("Unable to extract a leave start date for this start date.");
}
