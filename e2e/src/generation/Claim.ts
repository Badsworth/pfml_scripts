import EmployeePool, { Employee, EmployeePickSpec } from "./Employee";
import generateWorkPattern, { WorkPatternSpec } from "./WorkPattern";
import {
  Address,
  ApplicationLeaveDetails,
  ApplicationRequestBody,
  EmployerClaimRequestBody,
  PaymentPreference,
  PaymentPreferenceRequestBody,
  Phone,
  WorkPattern,
} from "../api";
import faker from "faker";
import generateLeaveDetails, { LeaveDetailsSpec } from "./LeaveDetails";
import { v4 as uuid } from "uuid";
import generateDocuments, {
  DehydratedDocument,
  DocumentGenerationSpec,
  DocumentWithPromisedFile,
} from "./documents";
import { pipeline, Readable } from "stream";
import fs from "fs";
import { promisify } from "util";
import path from "path";
import * as si from "streaming-iterables";
import ndjson from "ndjson";
import { StreamWrapper } from "./FileWrapper";
import { collect, map, AnyIterable } from "streaming-iterables";

const pipelineP = promisify(pipeline);
interface PromiseWithOptionalGeneration<T> extends Promise<T> {
  orGenerateAndSave(gen: () => T): Promise<T>;
}
/**
 * Specifies how a claim should be generated.
 */
export type ClaimSpecification = {
  /** A human-readable name or ID for this type of claim. */
  label: string;
  /** Reason for leave. */
  reason: ApplicationLeaveDetails["reason"];
  /** The qualifier for the leave reason */
  reason_qualifier?: ApplicationLeaveDetails["reason_qualifier"];
  /** An object describing documentation that should accompany the claim. */
  docs?: DocumentGenerationSpec;
  /** Describes the employer response that accompanies this claim */
  employerResponse?: GeneratedEmployerResponse;
  /** Specify an explicit address to use for the claim. */
  address?: Address;
  /** Specify explicit payment details to be used for the claim. */
  payment?: PaymentPreference;
  /**
   * Specifies work pattern. Can be one of "standard" or "rotating_shift", or a granular schedule in the format of
   * "0,240,240,0;240,0,0,0", where days are delineated by commas, weeks delineated by semicolon, and the numbers
   * are minutes worked on that day of the week (starting Sunday).
   */
  work_pattern_spec?: WorkPatternSpec;
  /** Optional metadata to be saved verbatim on the claim object. Not submitted in any way. */
  metadata?: GeneratedClaimMetadata;
} & LeaveDetailsSpec;

export type GeneratedClaimMetadata = Record<string, string | boolean>;

export type GeneratedEmployerResponse = Pick<
  EmployerClaimRequestBody,
  "hours_worked_per_week" | "employer_decision" | "fraud" | "comment"
>;

// Represents a single claim that will be issued to the system.
export type GeneratedClaim = {
  id: string;
  scenario: string;
  claim: ApplicationRequestBody;
  documents: DocumentWithPromisedFile[];
  employerResponse?: GeneratedEmployerResponse | null;
  paymentPreference: PaymentPreferenceRequestBody;
  metadata?: GeneratedClaimMetadata;
};

export type DehydratedClaim = Omit<GeneratedClaim, "documents"> & {
  documents: DehydratedDocument[];
};

/**
 * Responsible for generating single claims.
 */
export class ClaimGenerator {
  static generate(
    employeePool: EmployeePool,
    employeeSpec: EmployeePickSpec,
    spec: ClaimSpecification
  ): GeneratedClaim {
    const employee = employeePool.pick(employeeSpec);
    return this.generateFromEmployee(employee, spec);
  }
  static generateFromEmployee(
    employee: Employee,
    spec: ClaimSpecification
  ): GeneratedClaim {
    if (!employee.ssn) {
      throw new Error(
        "Malformed employee. Check that you have a valid employee pool"
      );
    }
    const address = spec.address ?? this.generateAddress();
    const workPattern = generateWorkPattern(spec.work_pattern_spec);
    const leaveDetails = generateLeaveDetails(spec, workPattern);
    // @todo: Later, we will want smarter logic for which occupation is picked.
    const occupation = employee.occupations[0];

    // All the complexity we know and love, just split up better.
    const claim: ApplicationRequestBody = {
      // These fields are brought directly over from the employee record.
      employment_status: "Employed",
      occupation: "Administrative",
      first_name: employee.first_name,
      last_name: employee.last_name,
      gender: "Prefer not to answer",
      tax_identifier: employee.ssn,
      employer_fein: occupation.fein,
      date_of_birth: employee.date_of_birth,
      has_state_id: !!employee.mass_id,
      mass_id: employee.mass_id ?? null,
      has_mailing_address: true,
      mailing_address: address,
      residential_address: address,
      hours_worked_per_week: this.calculateAverageWeeklyHours(workPattern),
      work_pattern: workPattern,
      phone: this.generatePhone(),
      leave_details: leaveDetails,
      has_continuous_leave_periods:
        (leaveDetails.continuous_leave_periods?.length ?? 0) > 0,
      has_reduced_schedule_leave_periods:
        (leaveDetails.reduced_schedule_leave_periods?.length ?? 0) > 0,
      has_intermittent_leave_periods:
        (leaveDetails.intermittent_leave_periods?.length ?? 0) > 0,
    };

    return {
      id: uuid(),
      // @todo: Rename to label?
      scenario: spec.label,
      claim,
      documents: generateDocuments(claim, spec.docs ?? {}),
      // @todo: It'd be nice if we just return a PaymentPreference here instead of PaymentPreferenceRequestBody...
      paymentPreference: {
        payment_preference: spec.payment ?? this.generatePaymentPreference(),
      },
      employerResponse: spec.employerResponse ?? null,
      metadata: spec.metadata,
    };
  }

  private static calculateAverageWeeklyHours(workPattern: WorkPattern): number {
    if (!workPattern.work_pattern_days) {
      return 40;
    }
    // Each item in the array is the number of minutes per week.
    const weeks: Array<number> = [];
    workPattern.work_pattern_days.forEach((workDay) => {
      // The week_number starts at 1, instead start at 0.
      const week_index = (workDay.week_number ?? 1) - 1;
      if (!(week_index in weeks)) {
        weeks[week_index] = 0;
      }
      weeks[week_index] = weeks[week_index] + (workDay.minutes || 0);
    });
    return weeks.reduce((a, b) => a + b) / weeks.length / 60;
  }

  private static generateAddress(): Address {
    return {
      city: faker.address.city(),
      line_1: faker.address.streetAddress(),
      state: faker.address.stateAbbr(),
      zip: faker.address.zipCode(),
    };
  }
  private static generatePhone(): Phone {
    return {
      int_code: "1",
      phone_number: "844-781-3163",
      phone_type: "Cell",
    };
  }
  private static generatePaymentPreference(): PaymentPreference {
    return {
      payment_method: "Elec Funds Transfer",
      account_number: "5555555555",
      routing_number: "011401533",
      bank_account_type: "Checking",
    };
  }

  /**
   * "Hydrate" a claim, turning it back into a normally generated claim.
   *
   * This is necessary after a claim has been dehydrated - the filename is replaced with callbacks that will
   * return a FileWrapper.
   */
  static async hydrate(
    claim: DehydratedClaim,
    directory: string
  ): Promise<GeneratedClaim> {
    const documents = claim.documents.map((document) => {
      const { file } = document;
      if (!(typeof file === "string")) {
        throw new Error(
          `Unknown file property. Expected a string, got a ${typeof file}`
        );
      }
      const fqp = path.join(directory, file);
      return {
        ...document,
        file: async () => {
          return new StreamWrapper(
            fs.createReadStream(fqp),
            path.basename(file)
          );
        },
      };
    });
    return {
      ...claim,
      documents,
    };
  }

  /**
   * "Dehydrate" a claim, making it possible to save to JSON format.
   *
   * This saves the claim's documents to disk, replacing the document "file" property with a string (filename).
   */
  static async dehydrate(
    claim: GeneratedClaim,
    directory: string
  ): Promise<DehydratedClaim> {
    const hydrateDocument = map(async (document: DocumentWithPromisedFile) => {
      if (typeof document.file !== "function") {
        throw new Error(
          `Expected to find a callback for this document's file. Instead, we found a ${typeof document.file}`
        );
      }
      const wrapper = await document.file();
      await pipelineP(
        wrapper.asStream(),
        fs.createWriteStream(path.join(directory, wrapper.filename))
      );
      return {
        ...document,
        file: wrapper.filename,
      };
    });
    return {
      ...claim,
      documents: await collect(hydrateDocument(claim.documents)),
    };
  }
}

/**
 * Claim Pools are storage devices for many claims at once.
 *
 * The claims they contain are "lazy", in the sense that they will only be generated or read from disk
 * at the time they are needed. This keeps the memory usage low, allowing us to generate, read, and write
 * huge pools of claims at once.
 */
export default class ClaimPool implements AsyncIterable<GeneratedClaim> {
  /**
   * Generate a new claim pool.
   */
  static generate(
    employeePool: EmployeePool,
    employeeSpec: EmployeePickSpec,
    claimSpec: ClaimSpecification,
    count: number
  ): ClaimPool {
    const claims = si.take(
      count,
      (function* () {
        while (true) {
          yield ClaimGenerator.generate(employeePool, employeeSpec, claimSpec);
        }
      })()
    );
    return new this(claims);
  }

  /**
   * Load a pool from NDJSON format.
   */
  static load(
    filename: string,
    documentDir: string
  ): PromiseWithOptionalGeneration<ClaimPool> {
    const loadPromise = (async () => {
      await fs.promises.access(filename, fs.constants.R_OK);
      const input = fs.createReadStream(filename).pipe(ndjson.parse());
      const hydrate = si.map((claim: DehydratedClaim) =>
        ClaimGenerator.hydrate(claim, documentDir)
      );
      return new this(hydrate(input));
    })();
    return Object.assign(loadPromise, {
      orGenerateAndSave: async (generator: () => ClaimPool) => {
        // When orGenerateAndSave() is called, return a new promise that adds a catch() to
        // the load promise to regenerate and save the data _only if the initial load fails_
        return loadPromise.catch(async (e) => {
          if (e.code !== "ENOENT") return Promise.reject(e);
          // Invoke the generator here, and save the pool it returns to `filename`
          const pool = await generator();
          await pool.save(filename, documentDir);
          return await ClaimPool.load(filename, documentDir);
        });
      },
    });
  }

  constructor(
    private claims: AsyncIterable<GeneratedClaim> | Iterable<GeneratedClaim>
  ) {}

  static merge(...pools: AnyIterable<GeneratedClaim>[]): ClaimPool {
    return new ClaimPool(si.merge(...pools));
  }

  /**
   * This function makes the claim pool iterable.
   */
  async *[Symbol.asyncIterator](): AsyncIterator<GeneratedClaim> {
    yield* this.claims;
  }

  /**
   * Return the claims in "dehydrated" format.
   *
   * This means the claim documents will be saved to disk, and the references replaced with
   * string file paths.
   *
   * @param documentDir
   */
  dehydrate(documentDir: string): AsyncIterable<DehydratedClaim> {
    const dehydrate = si.parallelMap(50, (claim: GeneratedClaim) => {
      return ClaimGenerator.dehydrate(claim, documentDir);
    });
    return dehydrate(this.claims);
  }

  /**
   * Save the pool to NDJSON format.
   */
  async save(filename: string, documentDir: string): Promise<void> {
    await pipelineP(
      Readable.from(this.dehydrate(documentDir)),
      ndjson.stringify(),
      fs.createWriteStream(filename)
    );
  }
}
