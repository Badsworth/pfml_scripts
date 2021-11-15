import { Employer } from "../Employer";
import { Employee, EmployeeOccupation } from "../Employee";
import { pipeline, Readable } from "stream";
import fs from "fs";
import { promisify } from "util";
import { endOfQuarter, format as formatDate, subQuarters } from "date-fns";

const pipelineP = promisify(pipeline);

// Date to fill in when no exemption is given.
const NO_EXEMPTION_DATE = "99991231";

const amt = (num: number): string => num.toFixed(2).padStart(20);

/**
 * Return an ISO date, given either a date object (already in ISO time), or a date string.
 * @param candidate
 */
function parseOrPassISODate(candidate: string | Date): Date {
  if (candidate instanceof Date) {
    return candidate;
  }
  const utc = new Date(candidate);
  return new Date(utc.getTime() + utc.getTimezoneOffset() * 1000 * 60);
}

/**
 * Generate a list of the last 4 quarters.
 * @param refDate
 * @param number
 */
const now = new Date();
function quarters(refDate = now, number = 4): Date[] {
  const quarters = [];

  for (let i = number; i > 0; i--) {
    quarters.push(endOfQuarter(subQuarters(refDate, i)));
  }
  return quarters;
}

/**
 * This class handles creation and formatting of DOR files from employee and employer pools.
 *
 * It uses NodeJS streams and generators in file generation, building up a generator function
 * that yields one line at a time. That line is written to a stream as soon as it is yielded,
 * preventing us from accumulating a lot of data in memory.
 *
 * For background reading on streams and generators:
 * @see https://nodejs.dev/learn/nodejs-streams
 * @see https://strongloop.com/strongblog/how-to-generators-node-js-yield-use-cases/
 */
export default class DOR {
  /**
   * Writes a single DOR "employers" file.
   */
  static async writeEmployersFile(
    employerPool: Iterable<Employer>,
    filename: string
  ): Promise<void> {
    // This is a generator function. It iterates through an EmployerPool, yielding one record at a time.
    const lines = function* () {
      for (const employer of employerPool) {
        yield DOR.formatEmployerLine(employer);
      }
    };
    return pipelineP(Readable.from(lines()), fs.createWriteStream(filename));
  }

  /**
   * Writes a single DOR "employees" file.
   */
  static async writeEmployeesFile(
    employerPool: Iterable<Employer>,
    employeePool: Iterable<Employee>,
    filename: string,
    refDate = now
  ): Promise<void> {
    const lines = function* () {
      const periods = quarters(refDate);
      const employerLookup = new Map<string, string>();
      for (const employer of employerPool) {
        employerLookup.set(employer.fein, employer.accountKey);
        yield* DOR.formatEmployeeEmployerLines(employer, periods);
      }
      for (const employee of employeePool) {
        for (const occupation of employee.occupations) {
          const accountKey = employerLookup.get(occupation.fein);
          if (!accountKey) {
            throw new Error(
              `Unable to find employer account key for ${occupation.fein}`
            );
          }
          yield* DOR.formatEmployeeEmployeeLines(
            employee,
            occupation,
            accountKey,
            periods
          );
        }
      }
    };

    return pipelineP(Readable.from(lines()), fs.createWriteStream(filename));
  }

  private static formatEmployerLine(employer: Employer): string {
    return (
      [
        employer.accountKey,
        employer.name.padEnd(255),
        employer.fein.replace(/-/g, "").padEnd(14),
        employer.street.padEnd(255),
        employer.city.padEnd(30),
        employer.state,
        employer.zip.replace(/-/g, ""),
        "USA",
        employer.dba.padEnd(255),
        // If both of these are set to true, the employer gets a special flag set
        // at the API (absenceManagement = False).
        employer.family_exemption ? "T" : "F",
        employer.medical_exemption ? "T" : "F",
        // Sets start date of leave plan.
        employer.exemption_commence_date
          ? formatDate(
              parseOrPassISODate(employer.exemption_commence_date),
              "yyyyMMdd"
            )
          : NO_EXEMPTION_DATE,
        // Not actually used at the moment.
        employer.exemption_cease_date
          ? formatDate(
              parseOrPassISODate(employer.exemption_cease_date),
              "yyyyMMdd"
            )
          : NO_EXEMPTION_DATE,
        formatDate(
          employer.updated_date
            ? parseOrPassISODate(employer.updated_date)
            : new Date(),
          "yyyyMMddHHmmss"
        ),
      ].join("") + "\n"
    );
  }

  private static formatEmployeeEmployerLines(
    employer: Employer,
    periods: Date[]
  ) {
    return periods.map((period, i) => {
      return (
        [
          "A",
          employer.accountKey,
          formatDate(period, "yyyyMMdd"),
          employer.name.padEnd(255),
          employer.fein.replace(/-/g, "").padEnd(14),
          "F",
          employer.fein.replace(/-/g, "").padEnd(14),
          amt(employer.withholdings?.[i] ?? 0),
          formatDate(period, "yyyyMMdd"),
          formatDate(period, "yyyyMMddHHmmss"),
        ].join("") + "\n"
      );
    });
  }

  private static formatEmployeeEmployeeLines(
    employee: Employee,
    occupation: EmployeeOccupation,
    accountKey: string,
    periods: Date[]
  ) {
    return periods.map((period, index) => {
      const quarterWages = occupation.wages / 4;
      return (
        [
          "B",
          accountKey,
          formatDate(period, "yyyyMMdd"),
          employee.first_name.padEnd(255),
          employee.last_name.padEnd(255),
          employee.ssn?.replace(/-/g, ""),
          "F", // Independent contractor.
          "T", // Opt-in
          // @todo: Toggle wages & contributions depending on the settings of the employee.
          amt((index + 1) * quarterWages), // Year to date Wages
          amt(quarterWages), // Quarterly wages.
          amt(0), //amt(record.employeeMedical),
          amt(0), //amt(record.employerMedical),
          amt(0), //amt(record.employeeFamily),
          amt(0), //amt(record.employerFamily)
        ].join("") + "\n"
      );
    });
  }
}
