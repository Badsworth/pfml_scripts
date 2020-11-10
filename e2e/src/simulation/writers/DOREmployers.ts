import stream from "stream";
import { Employer, SimulationClaim } from "../types";
import multipipe from "multipipe";
import util from "util";
import { formatISODate, formatISODatetime } from "../quarters";

// Date to fill in when no exemption is given.
const NO_EXEMPTION_DATE = "99991231";

export default function transformDOREmployers(
  employers: Map<string, Employer>
): stream.Duplex {
  const seen = new Set<string>();

  const pickEmployers = new stream.Transform({
    objectMode: true,
    // Collect every distinct employer in the set, first.
    write(chunk: SimulationClaim, encoding, callback) {
      if (chunk.claim.employer_fein && !seen.has(chunk.claim.employer_fein)) {
        seen.add(chunk.claim.employer_fein);
      }
      callback();
    },
    // Once we have every employer, fetch them from the employer storage and
    // pipe them to the next function.
    final(callback: (error?: Error | null) => void) {
      for (const id of seen.values()) {
        const employer = employers.get(id);
        if (!employer) {
          callback(new Error(`Unknown employer: ${id}`));
          return;
        }
        this.push(employer);
      }
      callback();
    },
  });

  const formatEmployerLines = new stream.Transform({
    objectMode: true,
    write(record: Employer, encoding, callback) {
      const line =
        util.format(
          "%s%s%s%s%s%s%s%s%s%s%s%s%s%s",
          record.accountKey,
          record.name.padEnd(255),
          record.fein.replace(/-/g, "").padEnd(14),
          record.street.padEnd(255),
          record.city.padEnd(30),
          record.state,
          record.zip.replace(/-/g, ""),
          "USA",
          record.dba.padEnd(255),
          record.family_exemption ? "T" : "F",
          record.medical_exemption ? "T" : "F",
          record.exemption_commence_date
            ? formatISODate(new Date(record.exemption_commence_date))
            : NO_EXEMPTION_DATE,
          record.exemption_cease_date
            ? formatISODate(new Date(record.exemption_cease_date))
            : NO_EXEMPTION_DATE,
          formatISODatetime(new Date(record.updated_date))
        ) + "\n";
      this.push(line);
      callback();
    },
  });

  return multipipe(pickEmployers, formatEmployerLines);
}
