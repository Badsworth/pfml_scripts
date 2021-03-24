import faker from "faker";
import fs from "fs";
import { formatISO } from "date-fns";
import unique from "./unique";
import { pipeline, Readable } from "stream";
import JSONStream from "JSONStream";
import { promisify } from "util";

const pipelineP = promisify(pipeline);

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
  exemption_commence_date?: Date | string;
  exemption_cease_date?: Date | string;
  updated_date?: Date | string;
  size?: "small" | "medium" | "large";
  withholdings: number[];
};

// Roulette wheel algorithm.
// Will generate 50x small employers and 10x medium employers for every large employer.
const employerSizeWheel = [
  ...new Array(50).fill("small"),
  ...new Array(10).fill("medium"),
  ...new Array(1).fill("large"),
];

type EmployerGenerationSpec = {
  size?: Employer["size"];
  withholdings?: (number | null)[]; // quarters with 0 or null withholding amounts
};

export class EmployerGenerator {
  private generateAccountKey = unique(() =>
    faker.helpers.replaceSymbolWithNumber("###########")
  );
  private generateCompanyName = unique(
    () =>
      `${faker.company
        .bs()
        .replace(/(^|\s|-)\w/g, (char) =>
          char.toUpperCase()
        )} ${faker.company.companySuffix()}`
  );
  private generateFEIN = unique(() =>
    faker.helpers.replaceSymbolWithNumber("##-#######")
  );
  private generateSize() {
    return employerSizeWheel[
      Math.floor(Math.random() * employerSizeWheel.length)
    ];
  }

  private generateWithholding(
    fein: string,
    spec: (number | null)[] = [null, null, null, null]
  ): Employer["withholdings"] {
    const formattedFein = fein.replace(/-/, "");
    const defaultWithholding = parseInt(formattedFein.slice(0, 6)) / 100;
    return spec.map((value) => value ?? defaultWithholding);
  }

  generate(spec: EmployerGenerationSpec = {}): Employer {
    // dba and name should be the same

    const name = this.generateCompanyName();
    const fein = this.generateFEIN();
    const withholdings = this.generateWithholding(fein, spec.withholdings);

    return {
      accountKey: this.generateAccountKey(),
      name,
      fein,
      street: faker.address.streetAddress(),
      city: faker.address.city(),
      state: "MA",
      zip: faker.address.zipCode("#####-####"),
      dba: name,
      family_exemption: false,
      medical_exemption: false,
      updated_date: formatISO(new Date()),
      size: spec.size ?? this.generateSize(),
      withholdings,
    };
  }
}

export default class EmployerPool implements Iterable<Employer> {
  private wheel?: number[];

  /**
   * Load a pool from a JSON file.
   */
  static async load(filename: string): Promise<EmployerPool> {
    const data = await fs.promises.readFile(filename, "utf-8");
    return new this(JSON.parse(data));
  }

  /**
   * Generate a new pool.
   */
  static generate(
    count: number,
    spec: EmployerGenerationSpec = {}
  ): EmployerPool {
    const generator = new EmployerGenerator();
    const employers = [...new Array(count)].map(() => generator.generate(spec));
    return new this(employers);
  }

  constructor(private employers: Employer[]) {}
  [Symbol.iterator](): Iterator<Employer> {
    return this.employers[Symbol.iterator]();
  }

  /**
   * Save the pool to JSON format.
   *
   * Uses streams for memory efficiency.
   */
  async save(filename: string): Promise<void> {
    await pipelineP(
      Readable.from(this.employers),
      JSONStream.stringify(),
      fs.createWriteStream(filename)
    );
  }

  /**
   * Merge one or more pools together into a megapool.
   *
   * @param pools
   */
  static merge(...pools: EmployerPool[]): EmployerPool {
    return new this(pools.map((p) => p.employers).flat(1));
  }

  /**
   * Pick a single employer from the pool.
   *
   * Favors larger employers, returning them more often.
   */
  pick(): Employer {
    if (this.employers.length === 0) {
      throw new Error("Cannot pick from an employer pool with no employers");
    }
    // Weighted picking logic - returns larger employers more often than smaller ones
    // using a roulette wheel algorithm.
    const wheel = this.getPickWheel();
    const i = wheel[Math.floor(Math.random() * wheel.length)];
    return this.employers[i];
  }

  private getPickWheel() {
    if (this.wheel) {
      return this.wheel;
    }
    return (this.wheel = this.employers.reduce((slots, employer, i) => {
      switch (employer.size) {
        case "large":
          // Large employers = 10x more employees than a small employer.
          return slots.concat(new Array(10).fill(i));
        case "medium":
          // Medium employers = 3x more employees than a small employer.
          return slots.concat(new Array(3).fill(i));
        default:
          // Also applies to "small" employers.
          return slots.concat([i]);
      }
    }, [] as number[]));
  }
}
