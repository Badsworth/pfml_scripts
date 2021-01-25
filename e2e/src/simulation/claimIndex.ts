import { SimulationClaim } from "./types";
import stream from "stream";
import csv from "csv-stringify";

export default function createClaimIndexStream(
  claims: SimulationClaim[]
): NodeJS.ReadableStream {
  const input = stream.Readable.from(
    (function* () {
      for (const simulationClaim of claims) {
        const { scenario, claim } = simulationClaim;
        const { first_name, last_name, tax_identifier, employer_fein } = claim;
        yield {
          scenario,
          first_name,
          last_name,
          tax_identifier,
          employer_fein,
        };
      }
    })()
  );
  return input.pipe(
    csv({
      header: true,
      columns: {
        scenario: "Scenario ID",
        first_name: "First Name",
        last_name: "Last Name",
        tax_identifier: "SSN",
        employer_fein: "Employer FEIN",
      },
    })
  );
}
