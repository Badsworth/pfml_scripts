import faker from "faker";
import fs from "fs";
import { formatISO } from "date-fns";
import unique from "./unique";
import { pipeline, Readable } from "stream";
import JSONStream from "JSONStream";
import { promisify } from "util";
import shuffle from "./shuffle";

const pipelineP = promisify(pipeline);

type EmployerSize = "small" | "medium" | "large";

export interface GeneratePromise<T> extends Promise<T> {
  orGenerateAndSave(generationCb: () => T): Promise<T>;
}

export type LoadOrGeneratePromise = GeneratePromise<EmployerPool>;

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
  size?: EmployerSize;
  withholdings: number[];
  metadata?: Record<string, unknown>;
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
  family_expemption?: boolean;
  medical_exemption?: boolean;
  exemption_commence_date?: Date;
  exemption_cease_date?: Date;
  metadata?: Record<string, unknown>;
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
      family_exemption: spec.family_expemption || false,
      medical_exemption: spec.medical_exemption || false,
      exemption_commence_date: spec.exemption_commence_date,
      exemption_cease_date: spec.exemption_cease_date,
      updated_date: formatISO(new Date()),
      size: spec.size ?? this.generateSize(),
      withholdings,
      metadata: spec.metadata ?? {},
    };
  }
}

export type EmployerPickSpec = {
  size?: EmployerSize;
  withholdings?: number[] | "exempt" | "non-exempt";
  notFEIN?: string;
  metadata?: Record<string, unknown>;
};

export default class EmployerPool implements Iterable<Employer> {
  private wheel?: EmployerSize[];

  /**
   * Load a pool from a JSON file.
   */
  static load(filename: string): LoadOrGeneratePromise {
    const employerProm = (async () => {
      const raw = await fs.promises.readFile(filename, "utf-8");
      return new this(JSON.parse(raw));
    })();
    return Object.assign(employerProm, {
      orGenerateAndSave: async (generator: () => EmployerPool) => {
        return employerProm.catch(async (e) => {
          if (e.code !== "ENOENT") throw e;
          const employerPool = generator();
          await employerPool.save(filename);
          return employerPool;
        });
      },
    });
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
  pick(spec: EmployerPickSpec = {}): Employer {
    // Filter the pool down based on spec. If an explicit size hasn't been given,
    // pick a size according to the chance defined by weightedSize().
    const filter = buildPickFilter({ size: this.weightedSize(), ...spec });
    const applicable = this.employers.filter(filter);
    const employer = shuffle(applicable).pop();
    if (!employer) {
      throw new Error(
        `No employers match the specification: ${JSON.stringify(spec)}`
      );
    }
    return employer;
  }

  /**
   * Use the roulette wheel algorithm to pick a particular size of employer to select from the pool.
   *
   * This function considers the sizes of the employers in the pool (it will not return "large" if there are no "large"
   * employers in the pool. Beyond that, it returns larger sizes more often.
   */
  private weightedSize(): EmployerSize {
    if (this.wheel === undefined) {
      // Pick out the distinct sizes of employers in the pool.
      const activeSizes = this.employers.reduce(
        (sizes, employer) => sizes.add(employer.size),
        new Set()
      );
      // Build a roulette wheel containing the sizes.
      const wheel: EmployerSize[] = [];
      activeSizes.forEach((size) => {
        switch (size) {
          case "small":
            // 1x chance of small.
            wheel.push(...new Array(1).fill("small"));
            break;
          case "medium":
            // 3x chance of medium.
            wheel.push(...new Array(3).fill("medium"));
            break;
          case "large":
            // 10x chance of large.
            wheel.push(...new Array(10).fill("large"));
            break;
        }
      });
      this.wheel = wheel;
    }
    return this.wheel[Math.floor(Math.random() * this.wheel.length)];
  }
}

function buildPickFilter(
  spec: EmployerPickSpec
): (employer: Employer) => boolean {
  return (employer: Employer) => {
    if (spec.notFEIN && spec.notFEIN === employer.fein) {
      return false;
    }
    if (spec.size && spec.size !== employer.size) {
      return false;
    }
    if (
      spec.withholdings === "exempt" &&
      employer.withholdings.some((amt) => amt > 0)
    ) {
      return false;
    }
    if (
      spec.withholdings === "non-exempt" &&
      employer.withholdings.some((amt) => amt === 0)
    ) {
      return false;
    }
    // Cheap test for shallow array equality.
    if (
      Array.isArray(spec.withholdings) &&
      JSON.stringify(employer.withholdings) !==
        JSON.stringify(spec.withholdings)
    ) {
      return false;
    }
    if (spec.metadata) {
      for (const [k, v] of Object.entries(spec.metadata)) {
        if (!employer.metadata || employer.metadata[k] !== v) {
          return false;
        }
      }
    }
    return true;
  };
}
