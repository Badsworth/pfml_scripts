import ClaimStateTracker from "../ClaimStateTracker";
import { GeneratedClaim } from "../../generation/Claim";
import { map } from "streaming-iterables";
import stringify from "csv-stringify";
import { promisify } from "util";
import { pipeline, Readable } from "stream";
import * as fs from "fs";
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
      },
    });
    await pipelineP(
      Readable.from(extract(claims)),
      formatter,
      fs.createWriteStream(filename)
    );
  }
}
