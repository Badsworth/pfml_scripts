import EmployerPool from "./Employer";
import fs from "fs";
import * as faker from "faker";
import unique from "./unique";
import { RandomSSN } from "ssn";
import { add, formatISO } from "date-fns";
import { promisify } from "util";
import { pipeline, Readable } from "stream";
import JSONStream from "JSONStream";
import shuffle from "./shuffle";

const pipelineP = promisify(pipeline);

export type EmployeeOccupation = {
  fein: string;
  wages: number;
};
export type Employee = {
  first_name: string;
  last_name: string;
  ssn: string;
  date_of_birth: string;
  occupations: EmployeeOccupation[];
  mass_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type WageSpecification =
  | "high"
  | "medium"
  | "low"
  | "eligible"
  | "ineligible"
  | number;

// Generate the min/max bounds for yearly wages.
function getWageBounds(spec: WageSpecification) {
  if (typeof spec === "number") {
    return [spec, spec];
  }
  switch (spec) {
    case "ineligible":
      return [2000, 5399];
    case "eligible":
      return [5400, 100000];
    case "high":
      return [90000, 100000];
    case "medium":
      return [30000, 90000];
    case "low":
      return [5400, 30000];
    default:
      throw new Error(`Invalid wage specification: ${spec}`);
  }
}
function wagesInBounds(wages: number, spec: WageSpecification): boolean {
  const [min, max] = getWageBounds(spec);
  return wages >= min && wages <= max;
}

type EmployeeGenerationSpec = {
  mass_id?: boolean;
  wages?: WageSpecification;
  metadata?: Record<string, unknown>;
};
export class EmployeeGenerator {
  static generate(
    employerPool: EmployerPool,
    spec: EmployeeGenerationSpec
  ): Employee {
    const occupations = this.generateOccupations(employerPool, spec.wages);
    return this.generateWithOccupations(occupations, spec);
  }
  static generateWithOccupations(
    occupations: EmployeeOccupation[],
    spec: EmployeeGenerationSpec
  ): Employee {
    return {
      first_name: faker.name.firstName(),
      last_name: faker.name.lastName(),
      ssn: this.generateSSN(),
      date_of_birth: this.generateDateOfBirth(),
      occupations: occupations,
      mass_id: spec.mass_id ? this.generateMassId() : null,
      metadata: spec.metadata,
    };
  }
  private static generateSSN = unique(() => {
    let ssn;
    do {
      ssn = new RandomSSN().value().toFormattedString();
    } while (ssn.startsWith("250-0"));
    return ssn;
  });
  private static generateOccupations(
    employerPool: EmployerPool,
    wages?: EmployeeGenerationSpec["wages"]
  ): EmployeeOccupation[] {
    const employer = employerPool.pick();
    return [
      {
        fein: employer.fein,
        wages: this.generateWages(wages),
      },
    ];
  }
  private static generateWages(
    spec: EmployeeGenerationSpec["wages"] = "eligible"
  ) {
    if (typeof spec === "number") {
      return spec;
    }
    const [min, max] = getWageBounds(spec);
    return faker.random.number({ min, max });
  }
  private static generateDateOfBirth(): string {
    // Generate a birthdate > 65 years ago and < 18 years ago.
    const dob = faker.date.between(
      add(new Date(), { years: -65 }),
      add(new Date(), { years: -18 })
    );
    return formatISO(dob, { representation: "date" });
  }
  // Generate a Mass ID number.
  static generateMassId(): string {
    return faker.random.arrayElement([
      faker.phone.phoneNumber("S########"),
      faker.phone.phoneNumber("SA#######"),
    ]);
  }
}

export type EmployeePickSpec = {
  // Whether or not the employee has a massachussetts ID #.
  mass_id?: boolean;
  // A specific wage specification that needs to be matched (# or level name).
  wages?: WageSpecification;
  metadata?: Record<string, unknown>;
};

export default class EmployeePool implements Iterable<Employee> {
  used: Set<string>;

  /**
   * Generate a new pool.
   */
  static generate(
    count: number,
    employers: EmployerPool,
    spec: EmployeeGenerationSpec
  ): EmployeePool {
    const employees = [...new Array(count)].map(() =>
      EmployeeGenerator.generate(employers, spec)
    );
    return new this(employees);
  }

  /**
   * Load a pool from a JSON file.
   */
  static async load(
    filename: string,
    usedFileName?: string
  ): Promise<EmployeePool> {
    // Do not use streams here. Interestingly, the perf/memory usage of this was tested,
    // and raw read/parse is faster and more efficient than the streams equivalent. ¯\_(ツ)_/¯
    let used = [];
    const raw = await fs.promises.readFile(filename, "utf-8");
    if (usedFileName) {
      const contents = await fs.promises.readFile(usedFileName, "utf-8");
      used = JSON.parse(contents);
    }
    return new this(JSON.parse(raw), used);
  }

  /**
   * Merge one or more pools together into a megapool.
   *
   * @param pools
   */
  static merge(...pools: EmployeePool[]): EmployeePool {
    return new this(pools.map((p) => p.employees).flat(1));
  }

  constructor(private employees: Employee[], used?: string[]) {
    this.used = new Set<string>(used);
  }

  /**
   * Save the pool to JSON format.
   */
  async save(filename: string, usedFileName?: string): Promise<void> {
    // Use streams for memory efficiency.
    await pipelineP(
      Readable.from(this.employees),
      JSONStream.stringify(),
      fs.createWriteStream(filename)
    );

    if (usedFileName) {
      await pipelineP(
        Readable.from(this.used),
        JSONStream.stringify(),
        fs.createWriteStream(usedFileName)
      );
    }
  }

  [Symbol.iterator](): Iterator<Employee> {
    return this.employees[Symbol.iterator]();
  }

  private _createFinder(
    spec: EmployeePickSpec
  ): (employee: Employee) => boolean {
    return (e) => {
      const wageSpec = spec.wages;
      const { metadata } = spec;
      // For each condition in the pick spec, return false if it is not met for this employee.
      if (
        wageSpec &&
        !e.occupations.some(({ wages }) => wagesInBounds(wages, wageSpec))
      ) {
        return false;
      }
      if (metadata) {
        for (const [k, v] of Object.entries(metadata)) {
          if (!e.metadata || e.metadata[k] !== v) {
            return false;
          }
        }
      }
      // If we've met all conditions, this is a matching employee.
      return true;
    };
  }

  /**
   * Filter the pool to a set that matches the specification.
   *
   * This will not modify the source pool, but will return a new "sub pool" containing only the matching employees.
   */
  filter(spec: EmployeePickSpec): EmployeePool {
    return new EmployeePool(this.employees.filter(this._createFinder(spec)));
  }

  /**
   * Shuffle the pool, randomizing the order.
   */
  shuffle(): EmployeePool {
    return new EmployeePool(shuffle(this.employees));
  }

  /**
   * Slice a number of Employees out of the pool.
   *
   * This will not remove these employees from the source pool, but will return a new "sub pool" containing only
   * those employees.
   */
  slice(start?: number, end?: number): EmployeePool {
    return new EmployeePool(this.employees.slice(start, end));
  }

  /**
   * Find one employee matching the specification.
   *
   * @param spec
   */
  find(spec: EmployeePickSpec): Employee | undefined {
    return this.employees.find(this._createFinder(spec));
  }

  /**
   * Pick a single employee from the pool.
   *
   * Note: this method tracks employee usage to avoid picking the same employee twice in a single data
   * generation session.
   */
  pick(spec: EmployeePickSpec): Employee {
    const finder = this._createFinder(spec);
    const employee = shuffle(this.employees).find((employee) => {
      return !this.used.has(employee.ssn) && finder(employee);
    });
    // Track employee usage.
    if (employee) {
      // Track the employee's usage.
      this.used.add(employee.ssn);
      return employee;
    }
    throw new Error(
      `No employee is left matching the specification: ${JSON.stringify(spec)}`
    );
  }
}
