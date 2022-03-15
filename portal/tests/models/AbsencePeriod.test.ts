import { AbsencePeriod } from "src/models/AbsencePeriod";
import LeaveReason from "src/models/LeaveReason";
import { faker } from "@faker-js/faker";

function createPeriod(customAttrs: Partial<AbsencePeriod> = {}) {
  return new AbsencePeriod({
    absence_period_start_date: "2021-01-01",
    absence_period_end_date: "2021-01-31",
    fineos_leave_request_id: faker.datatype.uuid(),
    request_decision: "Approved",
    reason: LeaveReason.medical,
    reason_qualifier_one: "",
    reason_qualifier_two: "",
    period_type: "Continuous",
    ...customAttrs,
  });
}

// Intentionally not sorted by start date or reason
const multipleLeaveReasonAbsencePeriods: AbsencePeriod[] = [
  createPeriod({
    absence_period_start_date: "2021-01-01",
    absence_period_end_date: "2021-01-31",
    reason: LeaveReason.medical,
  }),
  createPeriod({
    absence_period_start_date: "2021-03-01",
    absence_period_end_date: "2021-03-15",
    reason: LeaveReason.bonding,
  }),
  createPeriod({
    absence_period_start_date: "2021-02-01",
    absence_period_end_date: "2021-02-28",
    reason: LeaveReason.medical,
  }),
];

describe("AbsencePeriod", () => {
  it("#groupByReason groups periods by leave reason", () => {
    const groupedPeriods = AbsencePeriod.groupByReason(
      multipleLeaveReasonAbsencePeriods
    );

    expect(Object.keys(groupedPeriods)).toEqual([
      "Serious Health Condition - Employee",
      "Child Bonding",
    ]);
  });

  it("#groupByReason orders keys using the original ordering of periods", () => {
    const periodsOldToNew = [
      createPeriod({
        absence_period_start_date: "2021-01-01",
        absence_period_end_date: "2021-01-31",
        reason: LeaveReason.medical,
      }),
      createPeriod({
        absence_period_start_date: "2021-02-01",
        absence_period_end_date: "2021-02-28",
        reason: LeaveReason.bonding,
      }),
    ];
    const periodsNewToOld = AbsencePeriod.sortNewToOld(periodsOldToNew);

    expect(Object.keys(AbsencePeriod.groupByReason(periodsOldToNew))).toEqual([
      LeaveReason.medical,
      LeaveReason.bonding,
    ]);

    expect(Object.keys(AbsencePeriod.groupByReason(periodsNewToOld))).toEqual([
      LeaveReason.bonding,
      LeaveReason.medical,
    ]);
  });

  it("#sortNewToOld sorts periods from newest start to oldest start", () => {
    const startDates = AbsencePeriod.sortNewToOld(
      multipleLeaveReasonAbsencePeriods
    ).map((absencePeriod) => absencePeriod.absence_period_start_date);

    expect(startDates).toEqual(["2021-03-01", "2021-02-01", "2021-01-01"]);
  });

  it("#sortNewToOld does not mutate original periods array", () => {
    const sortedPeriods = AbsencePeriod.sortNewToOld(
      multipleLeaveReasonAbsencePeriods
    );

    expect(sortedPeriods).not.toEqual(multipleLeaveReasonAbsencePeriods);
  });
});
