import { WorkPattern } from "../api";

const daysOfWeek = [
  "Sunday" as const,
  "Monday" as const,
  "Tuesday" as const,
  "Wednesday" as const,
  "Thursday" as const,
  "Friday" as const,
  "Saturday" as const,
];

export type WorkPatternSpec =
  | "standard"
  | "rotating_shift"
  | "variable"
  | string;

export default function generateWorkPattern(
  spec: WorkPatternSpec = "standard"
): WorkPattern {
  // standard and rotating_shift are preformulated options
  switch (spec) {
    case "standard":
      return generateWorkPatternFromSpec("0,480,480,480,480,480,0");
    case "rotating_shift":
      return generateWorkPatternFromSpec("0,720,0,720,0,720,0;720,0,720,0,720");
    case "variable":
      return generateWorkPatternFromSpec("0,480,480,480,480,480,0", "Variable");
    default:
      return generateWorkPatternFromSpec(spec);
  }
}

function generateWorkPatternFromSpec(
  scheduleSpec: string,
  type?: WorkPattern["work_pattern_type"]
): WorkPattern {
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
    work_pattern_type: type || (weeks.length > 1 ? "Rotating" : "Fixed"),
    work_week_starts: "Monday",
    work_pattern_days: weeks.flat(),
  };
}
