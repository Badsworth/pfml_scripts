import stream from "stream";
import merge from "merge2";
import util from "util";
import { SimulationClaim } from "./types";

export type Employer = {
  accountKey: string;
  name: string;
  fein: string;
  street: string;
  city: string;
  state: string;
  zip: string;
  dba: string;
  family_exemption: boolean;
  medical_exemption: boolean;
  exemption_commence_date?: Date;
  exemption_cease_date?: Date;
  updated_date: Date;
};

function formatISODate(date: Date): string {
  return date.toISOString().split("T")[0].replace(/-/g, "");
}

/**
 * Returns a readable stream containing DOR employee filing lines.
 *
 * @param employers
 * @param filingPeriods
 */
function getEmployeeFilingRecords(
  employers: Employer[],
  filingPeriods: Date[]
): NodeJS.ReadableStream {
  const records = employers.reduce((records, employer) => {
    const thisEmployerRecords = filingPeriods.map((period) =>
      util.format(
        "A%s%s%s%s%s%s%s\n",
        employer.accountKey,
        formatISODate(period),
        employer.name.padEnd(255),
        employer.fein.replace(/-/g, ""),
        "F",
        formatISODate(period),
        formatISODate(period)
      )
    );
    return records.concat(thisEmployerRecords);
  }, [] as string[]);
  return stream.Readable.from(records);
}

/**
 * Returns a readable stream containing DOR employee wage lines.
 *
 * @param employees
 * @param employers
 * @param filingPeriods
 */
function getEmployeeWageRecords(
  claims: SimulationClaim[],
  employers: Employer[],
  filingPeriods: Date[]
): NodeJS.ReadableStream {
  const amt = (num: number): string => num.toFixed(2).padStart(20);

  const records = claims.reduce((records, claim) => {
    // Gets claim/emploee-specific data.
    const { claim: employee } = claim;
    // Determine the correct employer for this employee.
    const employer = employers.find((e) => e.fein === employee.employer_fein);
    if (!employer) {
      throw new Error(`Unable to find employer: ${employee.employer_fein}.`);
    }
    // Passes in wages that correspond to a financially (in)eligibile status.
    const quarterWages = claim.financiallyIneligible ? 1275 : 1276;
    const thisEmployeeRecords =
      filingPeriods.map((period, index): string => {
        return util.format(
          "B%s%s%s%s%s%s%s%s%s%s%s%s%s",
          employer.accountKey,
          formatISODate(period),
          employee.first_name?.padEnd(255),
          employee.last_name?.padEnd(255),
          employee.employee_ssn?.replace(/-/g, ""),
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
        );
      }) + "\n";
    return records.concat(thisEmployeeRecords);
  }, [] as string[]);

  return stream.Readable.from(records);
}

/**
 * Returns a readable stream containing DOR employee data lines.
 *
 * This data file will consist of two parts - the first one is the filing records that are represented in the
 * file (one per employer/filing period combo), and the second one is an employee wage line (one per employee/filing
 * period combo).
 *
 * @param employees
 * @param employers
 * @param filingPeriods
 */
export function createEmployeesStream(
  claims: SimulationClaim[],
  employers: Employer[],
  filingPeriods: Date[]
): NodeJS.ReadableStream {
  return merge(
    getEmployeeFilingRecords(employers, filingPeriods),
    getEmployeeWageRecords(claims, employers, filingPeriods)
  );
}

/**
 * Returns a readable stream containing DOR employer data lines.
 *
 * This file contains a line per employer.
 *
 * @param employers
 */
export function createEmployersStream(
  employers: Employer[]
): NodeJS.ReadableStream {
  return stream.Readable.from(
    (function* () {
      for (const record of employers) {
        yield util.format(
          "%s%s%s",
          record.accountKey,
          record.name.padEnd(255),
          record.fein.replace(/-/g, ""),
          record.street.padEnd(255),
          record.city.padEnd(30),
          record.state,
          record.zip,
          record.dba.padEnd(255),
          record.family_exemption ? "T" : "F",
          record.medical_exemption ? "T" : "F",
          record.exemption_commence_date
            ? formatISODate(record.exemption_commence_date)
            : "",
          record.exemption_cease_date
            ? formatISODate(record.exemption_cease_date)
            : "",
          formatISODate(record.updated_date)
        );
      }
    })()
  );
}
