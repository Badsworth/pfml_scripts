import {
  ApplicationLeaveDetails,
  ContinuousLeavePeriods,
  DayOfWeek,
  IntermittentLeavePeriods,
  ReducedScheduleLeavePeriods,
  WorkPattern,
} from "../api";
import {
  add,
  addDays,
  differenceInDays,
  format as formatDate,
  formatISO,
  max as maxDate,
  min as minDate,
  parseISO,
  subMonths,
} from "date-fns";
import faker from "faker";
import { ClaimSpecification } from "./Claim";

export default function generateLeaveDetails(
  config: ClaimSpecification,
  work_pattern: WorkPattern
): ApplicationLeaveDetails {
  const { reason, reason_qualifier } = config;
  const has_continuous_leave_periods =
    config.has_continuous_leave_periods ??
    (!config.reduced_leave_spec && !config.intermittent_leave_spec);
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
          config.reduced_leave_spec,
          config.leave_dates
        )
      : [],
    intermittent_leave_periods: config.intermittent_leave_spec
      ? generateIntermittentLeavePeriods(
          !!config.shortClaim,
          work_pattern,
          config.intermittent_leave_spec,
          config.leave_dates
        )
      : [],
    pregnant_or_recent_birth: !!config.pregnant_or_recent_birth,
    employer_notified: true,
    reason,
    reason_qualifier: reason_qualifier ?? null,
    caring_leave_metadata:
      reason === "Care for a Family Member"
        ? {
            relationship_to_caregiver: "Sibling - Brother/Sister",
            family_member_first_name: faker.name.firstName(),
            family_member_last_name: faker.name.lastName(),
            family_member_date_of_birth: formatISO(
              faker.date.between(
                add(new Date(), { years: -85 }),
                add(new Date(), { years: -10 })
              ),
              { representation: "date" }
            ),
          }
        : undefined,
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
    case "Care for a Family Member":
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

const formatISODate = (date: Date) =>
  formatISO(date, { representation: "date" });

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

type IntermittentLeaveSpec =
  | Partial<IntermittentLeavePeriods>
  | Partial<IntermittentLeavePeriods>[]
  | true;
function generateIntermittentLeavePeriods(
  shortLeave: boolean,
  work_pattern: WorkPattern,
  periods: IntermittentLeaveSpec,
  leave_dates?: [Date, Date]
): IntermittentLeavePeriods[] {
  const [startDate, endDate] =
    leave_dates ??
    generateLeaveDates(work_pattern, shortLeave ? { days: 7 } : undefined);
  const diffInDays = differenceInDays(endDate, startDate);
  const defaults: IntermittentLeavePeriods = {
    start_date: formatISO(startDate, { representation: "date" }),
    end_date: formatISO(endDate, { representation: "date" }),
    duration: faker.random.number({ min: 1, max: Math.min(diffInDays, 7) }),
    duration_basis: "Days",
    frequency: 1,
    frequency_interval: 1,
    frequency_interval_basis: "Weeks",
  };
  if (periods === true) {
    return [defaults];
  } else if (!Array.isArray(periods)) {
    return [{ ...defaults, ...periods }];
  } else {
    return periods.map((period) => ({ ...defaults, ...period }));
  }
}

function generateReducedLeavePeriods(
  shortLeave: boolean,
  work_pattern: WorkPattern,
  spec: string,
  leave_dates?: [Date, Date]
): ReducedScheduleLeavePeriods[] {
  const [startDate, endDate] =
    leave_dates ??
    generateLeaveDates(work_pattern, shortLeave ? { days: 1 } : undefined);

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

function makeChildPlacementDate(
  spec: ClaimSpecification["bondingDate"],
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
      return formatISODate(faker.date.between(new Date(), leaveStart));
    default:
      throw new Error(
        `Invalid bondingDate property given. You must set this property with one of "far-past", "past", or "future"`
      );
  }
}

// Generate an employer notification date based on the claim start date.
// Optionally, generate a "short notice" date.
function generateNotificationDate(startDate: Date, shortNotice: boolean) {
  return add(startDate, {
    days: shortNotice ? -1 : -60,
  });
}
