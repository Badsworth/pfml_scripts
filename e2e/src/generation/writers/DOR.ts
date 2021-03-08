import EmployerPool, { Employer } from "../Employer";
import EmployeePool, { Employee, EmployeeOccupation } from "../Employee";
import quarters, { parseOrPassISODate } from "../../simulation/quarters";
import { pipeline, Readable } from "stream";
import fs from "fs";
import { promisify } from "util";
import { format as formatDate } from "date-fns";

const pipelineP = promisify(pipeline);

// Date to fill in when no exemption is given.
const NO_EXEMPTION_DATE = "99991231";

const amt = (num: number): string => num.toFixed(2).padStart(20);

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
    employerPool: EmployerPool,
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
    employerPool: EmployerPool,
    employeePool: EmployeePool,
    filename: string
  ): Promise<void> {
    const lines = function* () {
      const periods = quarters();
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
        employer.family_exemption ? "T" : "F",
        employer.medical_exemption ? "T" : "F",
        employer.exemption_commence_date
          ? formatDate(
              parseOrPassISODate(employer.exemption_commence_date),
              "yyyyMMdd"
            )
          : NO_EXEMPTION_DATE,
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
    return periods.map((period) => {
      return (
        [
          "A",
          employer.accountKey,
          formatDate(period, "yyyyMMdd"),
          employer.name.padEnd(255),
          employer.fein.replace(/-/g, "").padEnd(14),
          "F",
          employer.fein.replace(/-/g, "").padEnd(14),
          amt(60000),
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
