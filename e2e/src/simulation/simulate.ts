import faker from "faker";
import {
  SimulationGenerator,
  ClaimDocument,
  SimulationGeneratorOpts,
} from "./types";
import { ApplicationRequestBody, ApplicationLeaveDetails } from "../api";
import generators from "./documents";
import path from "path";
import fs from "fs";
import { formatISO, subMonths, add } from "date-fns";

const formatISODate = (date: Date) =>
  formatISO(date, { representation: "date" });

export function chance(
  config: [number, SimulationGenerator][]
): SimulationGenerator {
  // Build up a "roulette wheel" consisting of array indices from this.generators.
  // Each generator gets N slices, where N = the generator's probability.
  // Slices are combined to form the final wheel.
  const wheel = config.reduce((partialWheel, [probability], i) => {
    const slices = new Array(probability).fill(i);
    return partialWheel.concat(slices);
  }, [] as number[]);

  return async function (opts) {
    // Pick a slice from the wheel.
    const sliceIdx = Math.floor(Math.random() * wheel.length);
    const generator = config[wheel[sliceIdx]][1];
    return generator(opts);
  };
}

type DocumentGenerators = typeof generators;
type ScenarioDocumentConfiguration = {
  [P in keyof DocumentGenerators]?: Parameters<DocumentGenerators[P]>[1] & {
    mailed?: boolean;
  };
};

export type ScenarioOpts = {
  reason: ApplicationLeaveDetails["reason"];
  reason_qualifier?: ApplicationLeaveDetails["reason_qualifier"];
  residence: "MA-proofed" | "MA-unproofed" | "OOS";
  financiallyIneligible?: boolean;
  employerExempt?: boolean;
  gaveAppropriateNotice?: boolean;
  docs: ScenarioDocumentConfiguration;
  skipSubmitClaim?: boolean;
  shortNotice?: boolean;
  bondingDate?: "far-past" | "past" | "future";
};

export function scenario(
  name: string,
  config: ScenarioOpts
): SimulationGenerator {
  return async (opts) => {
    const hasMassId =
      config.residence === "MA-proofed" || config.residence === "MA-unproofed";

    const employee = opts.employeeFactory(!!config.financiallyIneligible);

    const address = {
      city: faker.address.city(),
      line_1: faker.address.streetAddress(),
      state: faker.address.stateAbbr(),
      zip: faker.address.zipCode(),
    };

    const claim: ApplicationRequestBody = {
      // These fields are brought directly over from the employee record.
      employment_status: "Employed",
      occupation: "Administrative",
      first_name: employee.first_name,
      last_name: employee.last_name,
      tax_identifier: employee.tax_identifier,
      employer_fein: employee.employer_fein,
      date_of_birth: fmt(generateBirthDate()),
      has_state_id: hasMassId,
      mass_id: hasMassId ? generateMassIDString() : null,
      has_mailing_address: true,
      mailing_address: address,
      residential_address: address,
      hours_worked_per_week: 40,
      payment_preferences: [
        {
          payment_method: "Check",
          is_default: true,
          cheque_details: {
            name_to_print_on_check: `${employee.first_name} ${employee.last_name}`,
          },
        },
      ],
    };
    claim.leave_details = generateLeaveDetails(config);
    claim.has_continuous_leave_periods =
      (claim.leave_details?.continuous_leave_periods?.length ?? 0) > 0;
    claim.has_reduced_schedule_leave_periods =
      (claim.leave_details?.reduced_schedule_leave_periods?.length ?? 0) > 0;
    claim.has_intermittent_leave_periods =
      (claim.leave_details?.intermittent_leave_periods?.length ?? 0) > 0;

    return {
      scenario: name,
      claim,
      documents: await generateDocuments(claim, config, opts),
      financiallyIneligible: !!config.financiallyIneligible,
      // Flag for skipSubmitClaim.
      skipSubmitClaim: !!config.skipSubmitClaim,
    };
  };
}

export type AgentOpts = {
  priorityTask?: string;
  claim?: ApplicationRequestBody;
};
// For LST purposes, some scenarios do not need a claim or documents to be generated
export function agentScenario(
  name: string,
  config: AgentOpts = {}
): SimulationGenerator {
  return async () => {
    return {
      scenario: name,
      claim: {},
      documents: [],
      ...config,
    };
  };
}

/**
 * Generate all requested documents for a scenario.
 */
async function generateDocuments(
  claim: ApplicationRequestBody,
  config: ScenarioOpts,
  opts: SimulationGeneratorOpts
): Promise<ClaimDocument[]> {
  const dir = opts.documentDirectory;
  const docs = config.docs ?? ({} as ScenarioDocumentConfiguration);

  const promises = Object.entries(docs).map(async ([type, options]) => {
    if (!(type in generators)) {
      throw new Error(`Invalid document type: ${type}`);
    }
    // Cast document type to a const.
    const constType = type as keyof ScenarioDocumentConfiguration;
    // Pick the mailed property off of the options.
    const { mailed, ...actualOptions } = {
      mailed: false,
      ...options,
    } as Record<string, unknown>;
    const name = `${claim.tax_identifier}.${type}.pdf`;
    // Generate the document.
    await fs.promises.writeFile(
      path.join(dir, name),
      await generators[constType](claim, actualOptions)
    );
    return {
      type: constType,
      path: name,
      submittedManually: !!mailed,
    };
  });
  return Promise.all(promises);
}

function generateLeaveDetails(config: ScenarioOpts): ApplicationLeaveDetails {
  const { reason, reason_qualifier } = config;
  const [startDate, endDate] = generateLeaveDates();
  const notificationDate = generateNotificationDate(
    startDate,
    !!config.shortNotice
  );
  const details: ApplicationLeaveDetails = {
    continuous_leave_periods: [
      {
        start_date: fmt(startDate),
        end_date: fmt(endDate),
        is_estimated: true,
      },
    ],
    pregnant_or_recent_birth: false,
    employer_notification_date: fmt(notificationDate),
    employer_notified: true,
    reason,
    reason_qualifier,
  };
  switch (reason) {
    case "Serious Health Condition - Employee":
      // Do nothing else.
      break;
    case "Child Bonding":
      switch (reason_qualifier) {
        case "Newborn":
          details.child_birth_date = makeChildPlacementDate(
            config.bondingDate,
            startDate
          );
          details.pregnant_or_recent_birth = true;
          break;
        case "Adoption":
          details.child_placement_date = makeChildPlacementDate(
            config.bondingDate ?? "past",
            startDate
          );
          break;
        case "Foster Care":
          details.child_placement_date = makeChildPlacementDate(
            config.bondingDate ?? "past",
            startDate
          );
          break;
        default:
          throw new Error(`Invalid reason_qualifier for Child Bonding`);
      }
      break;
    default:
      throw new Error(`Invalid reason given`);
  }
  return details;
}

function makeChildPlacementDate(
  spec: ScenarioOpts["bondingDate"],
  leaveStart: Date
): string {
  switch (spec) {
    case "far-past":
      return formatISODate(
        faker.date.between(subMonths(new Date(), 13), subMonths(new Date(), 12))
      );
    case "past":
      // Recent birth date.
      return formatISODate(
        faker.date.between(subMonths(new Date(), 1), new Date())
      );
    case "future":
      // A date after 01-02-2021, but no more than startDate
      return formatISODate(
        faker.date.between(new Date("2021-01-01"), leaveStart)
      );
    default:
      throw new Error(
        `Invalid bondingDate property given. You must set this property with one of "far-past", "past", or "future"`
      );
  }
}

// Generate a Mass ID string.
function generateMassIDString(): string {
  return faker.random.arrayElement([
    faker.phone.phoneNumber("S########"),
    faker.phone.phoneNumber("SA#######"),
  ]);
}

// Generate start and end dates for a leave request, not to exceed 20 weeks, and with a minimum
// start date of 2021-01-01.
function generateLeaveDates(): [Date, Date] {
  const startDate = soon(182, "2021-01-01");
  const endDate = add(startDate, {
    weeks: faker.random.number({ min: 1, max: 11 }),
  });
  return [startDate, endDate];
}

// Generate an employer notification date based on the claim start date.
// Optionally, generate a "short notice" date.
function generateNotificationDate(startDate: Date, shortNotice: boolean) {
  return add(startDate, {
    days: shortNotice ? -1 : -60,
  });
}

// Generate a birthdate > 65 years ago and < 18 years ago.
function generateBirthDate(): Date {
  return faker.date.between(
    add(new Date(), { years: -65 }),
    add(new Date(), { years: -18 })
  );
}

// Replacement for faker.date.soon(), which is slated to be released in the future.
function soon(days: number, refDate?: string): Date {
  let date = new Date();
  if (typeof refDate !== "undefined") {
    date = new Date(Date.parse(refDate));
  }

  const range = {
    min: 1000,
    max: (days || 1) * 24 * 3600 * 1000,
  };

  let future = date.getTime();
  future += faker.random.number(range); // some time from now to N days later, in milliseconds
  date.setTime(future);

  return date;
}

function fmt(date: Date): string {
  return `${date.getFullYear()}-${(date.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${date.getDate().toString().padStart(2, "0")}`;
}
