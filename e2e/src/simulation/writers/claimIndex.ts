import stream from "stream";
import csv from "csv-stringify";
import { SimulationClaim } from "../types";
import multipipe from "multipipe";

export default function (): stream.Writable {
  const transform = new stream.Transform({
    objectMode: true,
    write(chunk: SimulationClaim, encoding, callback) {
      const { scenario, claim, wages } = chunk;
      const { first_name, last_name, tax_identifier, employer_fein } = claim;
      this.push({
        scenario,
        first_name,
        last_name,
        tax_identifier,
        employer_fein,
        wages,
      });
      callback();
    },
  });
  const csvStream = csv({
    header: true,
    columns: {
      scenario: "Scenario ID",
      first_name: "First Name",
      last_name: "Last Name",
      tax_identifier: "SSN",
      employer_fein: "Employer FEIN",
      wages: "Yearly Wages",
    },
  });

  return multipipe(transform, csvStream);
}
