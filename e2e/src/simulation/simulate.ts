import faker from "faker";
import {
  ClaimDocument,
  SimulationClaim,
  EmployerFactory,
  EmployeeFactory,
  SimulatedEmployerResponse,
  WageSpecification,
} from "./types";
import {
  ApplicationRequestBody,
  ApplicationLeaveDetails,
  ContinuousLeavePeriods,
  ReducedScheduleLeavePeriods,
  IntermittentLeavePeriods,
  WorkPattern,
  PaymentPreference,
  PaymentPreferenceRequestBody,
  Address,
  DayOfWeek,
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
  format as formatDate,
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
  employerExempt?: boolean;
  gaveAppropriateNotice?: boolean;
  docs: ScenarioDocumentConfiguration;
  employerResponse?: SimulatedEmployerResponse;
  skipSubmitClaim?: boolean;
  shortNotice?: boolean;
  has_continuous_leave_periods?: boolean;
  // Reduced leave can be specified in a specification. See work_pattern_spec for the expected
  // format.
  reduced_leave_spec?: string;
  has_intermittent_leave_periods?: boolean;
  pregnant_or_recent_birth?: boolean;
  bondingDate?: "far-past" | "past" | "future";
  leave_dates?: [Date, Date];
  address?: Address;
  payment?: PaymentPreference;
  // Specifies work pattern. Can be one of "standard" or "rotating_shift", or a granular
  // schedule in the format of "0,240,240,0;240,0,0,0", where days are delineated by commas,
  // weeks delineated by semicolon, and the numbers are minutes worked on that day of the week
  // (starting Sunday).
  work_pattern_spec?: "standard" | "rotating_shift" | string;
  // Makes a claim for an extremely short time period (1 day).
  shortClaim?: boolean;
  // For ID-proofing
  id_proof?: boolean;
  id_check?: string;
  wages?: WageSpecification;
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
      _config.wages ?? "eligible",
      opts.employerFactory
    );

    const address: Address = _config.address ?? {
      city: faker.address.city(),
      line_1: faker.address.streetAddress(),
      state: faker.address.stateAbbr(),
      zip: faker.address.zipCode(),
    };

    const workPattern = generateWorkPattern(_config.work_pattern_spec);
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

    const paymentPreferenceDetails: PaymentPreference = _config.payment ?? {
      payment_method: "Elec Funds Transfer",
      account_number: "5555555555",
      routing_number: "011401533",
      bank_account_type: "Checking",
    };

    const paymentPreference: PaymentPreferenceRequestBody = {
      payment_preference: paymentPreferenceDetails,
    };

    return {
      id: uuid(),
      scenario: name,
      claim,
      paymentPreference,
      employerResponse: _config.employerResponse,
      documents: await generateDocuments(claim, _config, opts),
      // Flag for skipSubmitClaim.
      skipSubmitClaim: !!_config.skipSubmitClaim,
      wages: employee.wages,
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
      wages: 0,
      ...config,
    };
    const _config = { ...config, ...opts };
    const employee = opts.employeeFactory("eligible", opts.employerFactory);
    defaultAgent.wages = employee.wages;
    defaultAgent.claim = {
      ..._config.claim,
      employer_fein: employee.employer_fein,
    };
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
export const generateWorkPatternFromSpec = (
  scheduleSpec: string
): WorkPattern => {
  const expandWeek = (week_number: number, ...minutesByDay: number[]) =>
    daysOfWeek.map((day_of_week, i) => ({
      day_of_week,
      minutes: minutesByDay[i] ?? 0,
      week_number,
    }));

  // Split schedule into weeks, then days, and build an array of the days.
  const weeks = scheduleSpec.split(";").map((weekSpec, weekIndex) => {
    const days = weekSpec.split(",").map((n) => parseInt(n));
    return expandWeek(weekIndex + 1, ...days);
  });

  return {
    work_pattern_type: weeks.length > 1 ? "Rotating" : "Fixed",
    work_week_starts: "Monday",
    work_pattern_days: weeks.flat(),
  };
};

function generateWorkPattern(
  spec: ScenarioOpts["work_pattern_spec"] = "standard"
): WorkPattern {
  // standard and rotating_shift are two options
  switch (spec) {
    case "standard":
      return generateWorkPatternFromSpec("0,480,480,480,480,480,0");
    case "rotating_shift":
      return generateWorkPatternFromSpec("0,720,0,720,0,720,0;720,0,720,0,720");
    default:
      return generateWorkPatternFromSpec(spec);
  }
}

function generateContinuousLeavePeriods(
  shortLeave: boolean,
  work_pattern: WorkPattern,
  leave_dates?: [Date, Date]
): ContinuousLeavePeriods[] {
  const [startDate, endDate] =
    leave_dates ??
    generateLeaveDates(work_pattern, shortLeave ? { days: 1 } : undefined);
  return [
    {
      start_date: formatISO(startDate, { representation: "date" }),
      end_date: formatISO(endDate, { representation: "date" }),
    },
  ];
}

function generateIntermittentLeavePeriods(
  shortLeave: boolean,
  work_pattern: WorkPattern
): IntermittentLeavePeriods[] {
  const [startDate, endDate] = generateLeaveDates(
    work_pattern,
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
  work_pattern: WorkPattern,
  spec: string
): ReducedScheduleLeavePeriods[] {
  const [startDate, endDate] = generateLeaveDates(
    work_pattern,
    shortLeave ? { days: 1 } : undefined
  );
  const minsByDay = spec
    // Split the spec into weeks (even though we only care about 1 week at a time here).
    .split(";")
    // Split the week into days and parse the minutes off.
    .map((weekSpec) => weekSpec.split(",").map((n) => parseInt(n)))
    // Only look at the first wek.
    .pop();

  if (!minsByDay || minsByDay.find(isNaN)) {
    throw new Error(`Invalid reduced leave specification: ${spec}`);
  }

  const getDayOffMinutes = (dayNumber: number) =>
    dayNumber in minsByDay ? minsByDay[dayNumber] : 0;

  return [
    {
      start_date: formatISO(startDate, { representation: "date" }),
      end_date: formatISO(endDate, { representation: "date" }),
      sunday_off_minutes: getDayOffMinutes(0),
      monday_off_minutes: getDayOffMinutes(1),
      tuesday_off_minutes: getDayOffMinutes(2),
      wednesday_off_minutes: getDayOffMinutes(3),
      thursday_off_minutes: getDayOffMinutes(4),
      friday_off_minutes: getDayOffMinutes(5),
      saturday_off_minutes: getDayOffMinutes(6),
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
  const has_continuous_leave_periods =
    config.has_continuous_leave_periods ||
    (!config.reduced_leave_spec && !config.has_intermittent_leave_periods);
  const details: ApplicationLeaveDetails = {
    continuous_leave_periods: has_continuous_leave_periods
      ? generateContinuousLeavePeriods(
          !!config.shortClaim,
          work_pattern,
          config.leave_dates
        )
      : [],
    reduced_schedule_leave_periods: config.reduced_leave_spec
      ? generateReducedLeavePeriods(
          !!config.shortClaim,
          work_pattern,
          config.reduced_leave_spec
        )
      : [],
    intermittent_leave_periods: config.has_intermittent_leave_periods
      ? generateIntermittentLeavePeriods(!!config.shortClaim, work_pattern)
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
    case "Pregnancy/Maternity":
      details.pregnant_or_recent_birth = true;
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

/**
 * Generate start and end dates for a leave request.
 *
 * Generated dates meet the following conditions:
 *   * Start date > max(2021-01-01, today) and < today + 60 days
 *   * End date < Start Date + 20 weeks.
 *   * Start date will always fall on a work day for this employee.
 */
export function generateLeaveDates(
  workPattern: WorkPattern,
  duration?: Duration
): [Date, Date] {
  // Start date must be greater than max(2021-01-01 or today).
  const minStartDate = maxDate([parseISO("2021-01-01"), new Date()]);
  // Start date must be < 60 days from the application date (now).
  const maxStartDate = addDays(new Date(), 60);

  const workingDays = (workPattern.work_pattern_days || [])
    .filter((day) => (day.minutes ?? 0) > 0)
    .map((day) => day.day_of_week);

  let i = 0;
  while (i++ < 100) {
    const startDate = faker.date.between(minStartDate, maxStartDate);
    // Leave dates MUST involve at least one day that falls in the work pattern.
    if (workingDays.includes(formatDate(startDate, "iiii") as DayOfWeek)) {
      // Allow duration overrides.
      const addition = duration ?? {
        weeks: faker.random.number({ min: 1, max: 11 }),
      };
      return [startDate, add(startDate, addition)];
    }
  }
  throw new Error("Unable to generate leave dates for this employee");
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
