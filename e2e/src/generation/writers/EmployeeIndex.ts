import { Employee, EmployeeOccupation } from "../Employee";
import { pipeline, Readable } from "stream";
import fs from "fs";
import { promisify } from "util";
import stringify from "csv-stringify";

const pipelineP = promisify(pipeline);

type HeaderProps = keyof Employee | keyof EmployeeOccupation;
type Headers = {
  [P in HeaderProps]?: string;
};

/**
 * Write a CSV "index" file of the employees in a dataset.
 */
export default class EmployeeIndex {
  static headers: Headers = {
    ssn: "SSN",
    first_name: "First Name",
    last_name: "Last Name",
    fein: "FEIN",
    wages: "Yearly Wages",
    metadata: "Metadata",
  };
  static async write(
    employees: Iterable<Employee>,
    filename: string
  ): Promise<void> {
    const lines = function* () {
      for (const employee of employees) {
        for (const occupation of employee.occupations) {
          yield {
            ...employee,
            ...occupation,
          };
        }
      }
    };
    return pipelineP(
      Readable.from(lines()),
      stringify({
        header: true,
        columns: this.headers as Record<string, string>,
      }),
      fs.createWriteStream(filename)
    );
  }
}
