import stream from "stream";
import { Employer, SimulationClaim } from "../types";
import { format } from "util";
import { format as formatDate } from "date-fns";
import multipipe from "multipipe";

const amt = (num: number): string => num.toFixed(2).padStart(20);

/**
 * Note: There's some weirdness with dates/formatting in this file.
 * Things to know about JS dates:
 *   * JS dates have no concept of timezone. They are always stored as UTC, and always output as local time.
 *   * When creating a date that only has a date (eg: 2020-01-01), UTC will be assumed (making the EST version 2019-12-31).
 * Because of this, we cannot detect what timezone a date was created with and adjust accordingly.
 * We must always assume that the date has been created in local time, and should always be output in local time.
 */

export function transformDOREmployeesEmployerLines(
  employers: Map<string, Employer>,
  filingPeriods: Date[]
): stream.Duplex {
  const seen = new Set<string>();
  const pickEmployers = new stream.Transform({
    objectMode: true,
    // Collect every distinct employer in the set, first.
    transform(chunk: SimulationClaim, encoding, callback) {
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

  const formatLines = new stream.Transform({
    objectMode: true,
    write(employer: Employer, encoding, callback) {
      const lines = filingPeriods.map((period) =>
        format(
          "A%s%s%s%s%s%s%s%s%s\n",
          employer.accountKey,
          formatDate(period, "yyyyMMdd"),
          employer.name.padEnd(255),
          employer.fein.replace(/-/g, "").padEnd(14),
          "F",
          employer.fein.replace(/-/g, "").padEnd(14),
          amt(60000),
          formatDate(period, "yyyyMMdd"),
          formatDate(period, "yyyyMMddHHmmss")
        )
      );
      this.push(lines.join(""));
      callback();
    },
  });
  return multipipe(pickEmployers, formatLines);
}

export function transformDOREmployeesWageLines(
  employers: Map<string, Employer>,
  filingPeriods: Date[]
): stream.Duplex {
  const transform = new stream.Transform({
    objectMode: true,
    transform(claim: SimulationClaim, encoding, callback) {
      // Gets claim/employee-specific data.
      const { claim: employee, wages } = claim;
      const employer = employers.get(claim.claim.employer_fein as string);
      if (!employer) {
        callback(
          new Error(
            `No employer found matching FEIN: ${claim.claim.employer_fein}`
          )
        );
        return;
      }
      if (!wages) {
        throw new Error(
          "Unable to generate due to missing wage data for employee"
        );
      }
      // Passes in wages that correspond to a financially (in)eligibile status.
      const quarterWages = wages / 4;
      const lines = filingPeriods.map((period, index): string => {
        return (
          format(
            "B%s%s%s%s%s%s%s%s%s%s%s%s%s",
            employer.accountKey,
            formatDate(period, "yyyyMMdd"),
            employee.first_name?.padEnd(255),
            employee.last_name?.padEnd(255),
            employee.tax_identifier?.replace(/-/g, ""),
            "F", // Independent contractor.
            "T", // Opt-in
            // @todo: Toggle wages & contributions depending on the settings of the employee.
            // ytdWages.
            amt((index + 1) * quarterWages),
            // quarterWages.
            amt(quarterWages),
            amt(0), //amt(record.employeeMedical),
            amt(0), //amt(record.employerMedical),
            amt(0), //amt(record.employeeFamily),
            amt(0) //amt(record.employerFamily)
          ) + "\n"
        );
      });
      this.push(lines.join(""));
      callback();
    },
  });
  return transform;
}
