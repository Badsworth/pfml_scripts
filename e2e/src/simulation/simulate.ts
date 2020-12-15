import faker from "faker";
import {
  ClaimDocument,
  SimulationClaim,
  EmployerFactory,
  EmployeeFactory,
} from "./types";
import {
  ApplicationRequestBody,
  ApplicationLeaveDetails,
  ContinuousLeavePeriods,
  ReducedScheduleLeavePeriods,
  IntermittentLeavePeriods,
  WorkPattern,
  PaymentPreference,
  Address,
} from "../api";
import generators from "./documents";
import path from "path";
import fs from "fs";
import {
  parseISO,
  formatISO,
  subMonths,
  add,
  addDays,
  max as maxDate,
  min as minDate,
  differenceInDays,
} from "date-fns";
import { v4 as uuid } from "uuid";

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
type IDCheckData = {
  first_name?: string;
  last_name?: string;
  tax_identifier?: string;
  employer_fein?: string;
  DOB?: string;
  massID?: string;
};

/**
 * SimulationGenerator is a function that generates a single SimulationClaim.
 */
export interface SimulationGenerator {
  // The generator returns a promise of a SimulationClaim so that it can
  // do asynchronous operations, like writing documents to the filesystem.
  (opts: GeneratorOpts): Promise<SimulationClaim>;
}
export type GeneratorOpts = Partial<ScenarioOpts> & {
  documentDirectory: string;
  employeeFactory: EmployeeFactory;
  employerFactory: EmployerFactory;
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
  has_continuous_leave_periods?: boolean;
  has_reduced_schedule_leave_periods?: boolean;
  has_intermittent_leave_periods?: boolean;
  pregnant_or_recent_birth?: boolean;
  bondingDate?: "far-past" | "past" | "future";
  work_pattern_type?: "standard" | "rotating_shift";
  // Makes a claim for an extremely short time period (1 day).
  shortClaim?: boolean;
  // For ID-proofing
  id_proof?: boolean;
  id_check?: string;
};

export function scenario(
  name: string,
  config: ScenarioOpts
): SimulationGenerator {
  return async (opts) => {
    // Allow opts to overide config.
    const _config = { ...config, ...opts };
    const hasMassId =
      _config.residence === "MA-proofed" ||
      _config.residence === "MA-unproofed";
    let IDData: IDCheckData = {};

    if (config.id_proof) {
      IDData = getIDData(config.id_check as string);
    }

    const employee = opts.employeeFactory(
      !!_config.financiallyIneligible,
      opts.employerFactory
    );

    const address: Address = {
      city: faker.address.city(),
      line_1: faker.address.streetAddress(),
      state: faker.address.stateAbbr(),
      zip: faker.address.zipCode(),
    };

    const workPattern = generateWorkPattern(_config.work_pattern_type);
    const claim: ApplicationRequestBody = {
      // These fields are brought directly over from the employee record.
      employment_status: "Employed",
      occupation: "Administrative",
      first_name: config.id_proof ? IDData.first_name : employee.first_name,
      last_name: config.id_proof ? IDData.last_name : employee.last_name,
      tax_identifier: config.id_proof
        ? IDData.tax_identifier
        : employee.tax_identifier,
      employer_fein: config.id_proof
        ? IDData.employer_fein
        : employee.employer_fein,
      date_of_birth: config.id_proof
        ? IDData.DOB
        : formatISO(generateBirthDate(), { representation: "date" }),
      has_state_id: hasMassId,
      mass_id:
        hasMassId || config.id_proof
          ? generateMassIDString(
              config.id_proof as boolean,
              config.id_check as string
            )
          : null,
      has_mailing_address: true,
      mailing_address: config.id_proof
        ? getIDCheckAddress(config.id_check as string)
        : address,
      residential_address: config.id_proof
        ? getIDCheckAddress(config.id_check as string)
        : address,
      hours_worked_per_week: 40,
      work_pattern: workPattern,
      phone: {
        int_code: "1",
        phone_number: "844-781-3163",
        phone_type: "Cell",
      },
    };
    claim.leave_details = generateLeaveDetails(_config, workPattern);
    claim.has_continuous_leave_periods =
      (claim.leave_details?.continuous_leave_periods?.length ?? 0) > 0;
    claim.has_reduced_schedule_leave_periods =
      (claim.leave_details?.reduced_schedule_leave_periods?.length ?? 0) > 0;
    claim.has_intermittent_leave_periods =
      (claim.leave_details?.intermittent_leave_periods?.length ?? 0) > 0;

    const paymentPreference: PaymentPreference = {
      payment_method: "Debit",
      account_number: "5555555555",
      routing_number: "011401533",
      bank_account_type: "Savings",
    };

    return {
      id: uuid(),
      scenario: name,
      claim,
      paymentPreference: paymentPreference,
      documents: await generateDocuments(claim, _config, opts),
      financiallyIneligible: !!_config.financiallyIneligible,
      // Flag for skipSubmitClaim.
      skipSubmitClaim: !!_config.skipSubmitClaim,
    };
  };
}

export type AgentOpts = {
  priorityTask?: string;
  claim?: ApplicationRequestBody;
};

export function getIDData(idCheck: string): IDCheckData {
  switch (idCheck) {
    case "valid":
    case "mismatch":
      return {
        first_name: "John",
        last_name: "Pinkham",
        tax_identifier: "020-52-0105",
        employer_fein: "77-4586523",
        DOB: "1973-10-30",
        massID: "S46493908",
      };

    case "fraud":
      return {
        first_name: "Willis",
        last_name: "Sierra",
        tax_identifier: "646-85-9053",
        employer_fein: "77-4586523",
        DOB: "1975-06-02",
        massID: "SA2600200",
      };

    case "invalid":
      return {
        first_name: "Steve",
        last_name: "Tester",
        tax_identifier: "291-81-2020",
        employer_fein: "77-4586523",
        DOB: "1965-09-16",
        massID: "SA0010000",
      };

    default:
      throw new Error("No ID check Found!");
  }
}

export function getIDCheckAddress(idCheck: string): Address {
  switch (idCheck) {
    case "valid":
      return {
        city: "ashfield",
        line_1: "83g bear mountain dr",
        state: "MA",
        zip: "01330",
      };

    case "fraud":
      return {
        city: "lynn",
        line_1: "42 murray st",
        state: "MA",
        zip: "01905",
      };

    case "invalid":
      return {
        city: "quincy",
        line_1: "25 newport avenue ext",
        state: "MA",
        zip: "02171",
      };

    default:
      return {
        city: faker.address.city(),
        line_1: faker.address.streetAddress(),
        state: faker.address.stateAbbr(),
        zip: faker.address.zipCode(),
      };
  }
}

// For LST purposes, some scenarios do not need a claim or documents to be generated
export function agentScenario(
  name: string,
  config: AgentOpts = {}
): SimulationGenerator {
  return async (opts) => {
    const defaultAgent = {
      id: uuid(),
      scenario: name,
      claim: {},
      paymentPreference: {},
      documents: [],
      ...config,
    };
    if (config.claim?.employer_fein) {
      const _config = { ...config, ...opts };
      const employee = opts.employeeFactory(
        !!_config.financiallyIneligible,
        opts.employerFactory
      );
      defaultAgent.claim = {
        ..._config.claim,
        employer_fein: employee.employer_fein,
      };
    }
    return defaultAgent;
  };
}

/**
 * Generate all requested documents for a scenario.
 */
async function generateDocuments(
  claim: ApplicationRequestBody,
  config: ScenarioOpts,
  opts: GeneratorOpts
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

const daysOfWeek = [
  "Sunday" as const,
  "Monday" as const,
  "Tuesday" as const,
  "Wednesday" as const,
  "Thursday" as const,
  "Friday" as const,
  "Saturday" as const,
];
function makeWeeklySchedule(week_number: number, ...hoursByDay: number[]) {
  return daysOfWeek.map((day_of_week, i) => ({
    day_of_week,
    minutes: (hoursByDay[i] ?? 0) * 60,
    week_number,
  }));
}
function generateWorkPattern(
  type: ScenarioOpts["work_pattern_type"] = "standard"
): WorkPattern {
  switch (type) {
    case "standard":
      return {
        work_pattern_type: "Fixed",
        work_week_starts: "Monday",
        work_pattern_days: makeWeeklySchedule(1, 0, 8, 8, 8, 8, 8, 0),
      };
    case "rotating_shift":
      return {
        work_pattern_type: "Rotating",
        work_week_starts: "Monday",
        work_pattern_days: [
          ...makeWeeklySchedule(1, 0, 12, 0, 12, 0, 12),
          ...makeWeeklySchedule(2, 12, 0, 12, 0, 12),
        ],
      };
    default:
      throw new Error(
        `Unsure of how to generate a work pattern for ${type} type.`
      );
  }
}

function generateContinuousLeavePeriods(
  shortLeave: boolean
): ContinuousLeavePeriods[] {
  const [startDate, endDate] = generateLeaveDates(
    shortLeave ? { days: 1 } : undefined
  );
  return [
    {
      start_date: formatISO(startDate, { representation: "date" }),
      end_date: formatISO(endDate, { representation: "date" }),
    },
  ];
}

function generateIntermittentLeavePeriods(
  shortLeave: boolean
): IntermittentLeavePeriods[] {
  const [startDate, endDate] = generateLeaveDates(
    shortLeave ? { days: 7 } : undefined
  );
  const diffInDays = differenceInDays(endDate, startDate);

  return [
    {
      start_date: formatISO(startDate, { representation: "date" }),
      end_date: formatISO(endDate, { representation: "date" }),
      duration: faker.random.number({ min: 1, max: Math.min(diffInDays, 7) }),
      duration_basis: "Days",
      frequency: 1,
      frequency_interval: 1,
      frequency_interval_basis: "Weeks",
    },
  ];
}

function generateReducedLeavePeriods(
  shortLeave: boolean,
  work_pattern: WorkPattern
): ReducedScheduleLeavePeriods[] {
  const [startDate, endDate] = generateLeaveDates(
    shortLeave ? { days: 1 } : undefined
  );
  function getDayOffMinutes(dayName: string): number {
    const dayObj = (work_pattern.work_pattern_days ?? [])
      .filter((day) => day.day_of_week == dayName && day.week_number === 1)
      .pop();
    return dayObj && dayObj.minutes ? dayObj.minutes / 2 : 0;
  }
  return [
    {
      start_date: formatISO(startDate, { representation: "date" }),
      end_date: formatISO(endDate, { representation: "date" }),
      sunday_off_minutes: getDayOffMinutes("Sunday"),
      monday_off_minutes: getDayOffMinutes("Monday"),
      tuesday_off_minutes: getDayOffMinutes("Tuesday"),
      wednesday_off_minutes: getDayOffMinutes("Wednesday"),
      thursday_off_minutes: getDayOffMinutes("Thursday"),
      friday_off_minutes: getDayOffMinutes("Friday"),
      saturday_off_minutes: getDayOffMinutes("Saturday"),
    },
  ];
}

function getEarliestStartDate(details: ApplicationLeaveDetails): Date {
  const leaveDates: Date[] = [];

  const leavePeriods = [
    details.continuous_leave_periods as ContinuousLeavePeriods[],
    details.reduced_schedule_leave_periods as ReducedScheduleLeavePeriods[],
    details.intermittent_leave_periods as IntermittentLeavePeriods[],
  ];
  leavePeriods.forEach((period) => {
    if (period === undefined || period.length < 1) {
      return;
    }
    leaveDates.push(parseISO(period[0].start_date as string));
  });
  if (leaveDates.length < 1)
    throw new Error("No leave dates have been specified");
  return minDate(leaveDates);
}

function generateLeaveDetails(
  config: ScenarioOpts,
  work_pattern: WorkPattern
): ApplicationLeaveDetails {
  const { reason, reason_qualifier } = config;
  const details: ApplicationLeaveDetails = {
    continuous_leave_periods:
      !config.has_reduced_schedule_leave_periods &&
      !config.has_intermittent_leave_periods
        ? generateContinuousLeavePeriods(!!config.shortClaim)
        : [],
    reduced_schedule_leave_periods: config.has_reduced_schedule_leave_periods
      ? generateReducedLeavePeriods(!!config.shortClaim, work_pattern)
      : [],
    intermittent_leave_periods: config.has_intermittent_leave_periods
      ? generateIntermittentLeavePeriods(!!config.shortClaim)
      : [],
    pregnant_or_recent_birth: !!config.pregnant_or_recent_birth,
    employer_notified: true,
    reason,
    reason_qualifier,
  };

  const earliestStartDate = getEarliestStartDate(details);

  details.employer_notification_date = formatISO(
    generateNotificationDate(earliestStartDate, !!config.shortNotice),
    { representation: "date" }
  );

  switch (reason) {
    case "Serious Health Condition - Employee":
      // Do nothing else.
      break;
    case "Child Bonding":
      switch (reason_qualifier) {
        case "Newborn":
          details.child_birth_date = makeChildPlacementDate(
            config.bondingDate,
            earliestStartDate
          );
          details.pregnant_or_recent_birth = true;
          break;
        case "Adoption":
          details.child_placement_date = makeChildPlacementDate(
            config.bondingDate ?? "past",
            earliestStartDate
          );
          break;
        case "Foster Care":
          details.child_placement_date = makeChildPlacementDate(
            config.bondingDate ?? "past",
            earliestStartDate
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
function generateMassIDString(idProof: boolean, idCheck: string): string {
  if (idProof) {
    switch (idCheck) {
      case "valid":
        return "S46493908";
    }
  }
  return faker.random.arrayElement([
    faker.phone.phoneNumber("S########"),
    faker.phone.phoneNumber("SA#######"),
  ]);
}

// Generate start and end dates for a leave request, not to exceed 20 weeks, and with a minimum
// start date of 2021-01-01.
export function generateLeaveDates(duration?: Duration): [Date, Date] {
  // Start date must be greater than max(2021-01-01 or today).
  const minStartDate = maxDate([parseISO("2021-01-01"), new Date()]);
  // Start date must be < 60 days from the application date (now).
  const maxStartDate = addDays(new Date(), 60);

  const startDate = faker.date.between(minStartDate, maxStartDate);

  // If the claim is marked as "short leave", give it a 1 day length.
  const addition = duration ?? {
    weeks: faker.random.number({ min: 1, max: 11 }),
  };
  return [startDate, add(startDate, addition)];
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
