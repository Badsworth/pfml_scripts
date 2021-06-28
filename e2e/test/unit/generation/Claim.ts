import { afterAll, beforeAll, expect, it, jest } from "@jest/globals";
import generateDocuments from "../../../src/generation/documents";
import ClaimPool, {
  ClaimGenerator,
  ClaimSpecification,
  EmployerResponseSpec,
  GeneratedClaim,
} from "../../../src/generation/Claim";
import EmployeePool from "../../../src/generation/Employee";
import { extractLeavePeriod } from "../../../src/util/claims";
import fs from "fs";
import path from "path";
import os from "os";
import { mocked } from "ts-jest/utils";
import { Uint8ArrayWrapper } from "../../../src/generation/FileWrapper";
import dataDirectory, {
  DataDirectory,
} from "./../../../src/generation/DataDirectory";
import { EmployerBenefit, OtherIncome, PreviousLeave } from "../../../src/_api";
import {
  differenceInCalendarWeeks,
  parseISO,
  isSunday,
  isAfter,
} from "date-fns";
import { getCaringLeaveStartEndDates } from "../../../src/util/claims";
import {
  assertIsTypedArray,
  isValidPreviousLeave,
} from "../../../src/util/typeUtils";

jest.mock("../../../src/generation/documents");
const generateDocumentsMock = mocked(generateDocuments);

jest.mock("../../../src/generation/Employee");

const START_LEAVE = "2021-03-05";
const END_LEAVE = "2021-04-05";

const benefitWithExplicitDates: EmployerBenefit = {
  benefit_amount_dollars: 1000,
  benefit_amount_frequency: "Per Month",
  benefit_type: "Family or medical leave insurance",
  benefit_end_date: "2021-01-01",
  benefit_start_date: "2021-02-01",
};
const benefitWithoutDates: EmployerBenefit = {
  benefit_amount_dollars: 200,
  benefit_amount_frequency: "Per Week",
  benefit_type: "Short-term disability insurance",
};
const previousLeave: PreviousLeave = {
  is_for_current_employer: true,
  type: "same_reason",
  leave_reason: "Bonding with my child after birth or placement",
  leave_minutes: 9600,
  worked_per_week_minutes: 2400,
  leave_end_date: "2021-02-01",
  leave_start_date: "2021-01-01",
};
const previousLeaveWithoutDates: PreviousLeave = {
  is_for_current_employer: true,
  type: "other_reason",
  leave_minutes: 9600,
  worked_per_week_minutes: 2400,
  leave_reason: "Pregnancy",
};
const otherIncomeWithoutDates: OtherIncome = {
  income_type: "SSDI",
  income_amount_dollars: 100,
  income_amount_frequency: "Per Week",
};
const otherIncomeWithDates: OtherIncome = {
  income_type: "SSDI",
  income_amount_dollars: 100,
  income_amount_frequency: "Per Week",
  income_end_date: "2021-01-01",
  income_start_date: "2021-02-01",
};

const medical: ClaimSpecification = {
  label: "Medical",
  reason: "Serious Health Condition - Employee",
  reason_qualifier: null,
  docs: {
    HCP: {},
    MASSID: {},
  },
  metadata: { hasMetadata: true },
};
const bonding: ClaimSpecification = {
  label: "Bonding",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
};
const reduced: ClaimSpecification = {
  label: "Reduced",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
  work_pattern_spec: "standard",
  reduced_leave_spec: "0,240,240,240,240,240,0",
};

const reduced_explicit_dates: ClaimSpecification = {
  label: "Reduced",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  leave_dates: [parseISO(START_LEAVE), parseISO(END_LEAVE)],
  docs: {
    HCP: {},
    MASSID: {},
  },
  work_pattern_spec: "standard",
  reduced_leave_spec: "0,240,240,240,240,240,0",
};
const intermittent: ClaimSpecification = {
  label: "Intermittent",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
  intermittent_leave_spec: true,
};
const intermittent_explicit_dates: ClaimSpecification = {
  label: "Intermittent",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
  intermittent_leave_spec: true,
  leave_dates: [parseISO(START_LEAVE), parseISO(END_LEAVE)],
};
const payments: ClaimSpecification = {
  label: "Payments",
  reason: "Serious Health Condition - Employee",
  has_continuous_leave_periods: true,
  leave_dates: [parseISO("2021-01-01"), parseISO("2021-02-01")],
  address: {
    city: "City",
    line_1: "123 Street Road",
    state: "MA",
    zip: "00000",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  docs: {},
};

const employee = {
  first_name: "John",
  last_name: "Smith",
  ssn: "000-00-0000",
  date_of_birth: "2020-01-01",
  occupations: [{ fein: "12-34567", wages: 10000 }],
};

let storage: DataDirectory;
const EMPLOYEE_TEST_DIR = "/employee_unit_test";
const prepareStorage = async () => {
  storage = dataDirectory(EMPLOYEE_TEST_DIR);
  await storage.prepare();
};

const [start, end] = getCaringLeaveStartEndDates();
const caring_leave_dates: ClaimSpecification = {
  label: "Testing Caring Leave Dates",
  reason: "Care for a Family Member",
  work_pattern_spec: "0,720,0,720,0,720,0",
  docs: {},
  leave_dates: [start, end],
};

const removeStorage = async () => {
  await fs.promises.rmdir(storage.dir, { recursive: true });
};
describe("Claim Generator", () => {
  let employeePool: EmployeePool;

  beforeEach(() => {
    jest.clearAllMocks();
    employeePool = new EmployeePool([employee]);
    mocked(employeePool).pick.mockImplementation(() => employee);
  });

  it("Should generate a unique ID for each simulation claim", async () => {
    const claim1 = ClaimGenerator.generate(employeePool, {}, medical);
    const claim2 = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim1).toHaveProperty("id", expect.any(String));
    expect(claim2).toHaveProperty("id", expect.any(String));
    expect(claim1.id).not.toEqual(claim2.id);
  });

  it("Should have claim properties", async () => {
    const claim = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim.scenario).toEqual("Medical");
    expect(claim.metadata).toEqual({ hasMetadata: true });
    expect(claim.claim).toMatchObject({
      employment_status: "Employed",
      first_name: expect.any(String),
      last_name: expect.any(String),
      tax_identifier: employee.ssn,
      date_of_birth: employee.date_of_birth,
    });
  });

  it("Should pass arguments to the employee factory", async () => {
    const spec = { wages: 200 };
    ClaimGenerator.generate(employeePool, spec, medical);
    expect(mocked(employeePool).pick).toHaveBeenCalledTimes(1);
    expect(mocked(employeePool).pick).toHaveBeenCalledWith(spec);
  });

  it("Should populate the mass_id property for mass proofed claims", async () => {
    mocked(employeePool).pick.mockImplementationOnce(() => ({
      ...employee,
      mass_id: "123",
    }));
    const claim = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim.claim.mass_id).toEqual("123");
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should not populate the mass_id property for OOS claims", async () => {
    const claim = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim.claim.mass_id).toBe(null);
    expect(claim.claim.has_state_id).toBe(false);
  });

  it("Should have has_ properties that match its leave periods", async () => {
    expect(ClaimGenerator.generate(employeePool, {}, medical)).toMatchObject({
      claim: {
        has_continuous_leave_periods: true,
        has_intermittent_leave_periods: false,
        has_reduced_schedule_leave_periods: false,
      },
    });
    expect(
      ClaimGenerator.generate(employeePool, {}, intermittent)
    ).toMatchObject({
      claim: {
        has_continuous_leave_periods: false,
        has_intermittent_leave_periods: true,
        has_reduced_schedule_leave_periods: false,
      },
    });
    expect(ClaimGenerator.generate(employeePool, {}, reduced)).toMatchObject({
      claim: {
        has_continuous_leave_periods: false,
        has_intermittent_leave_periods: false,
        has_reduced_schedule_leave_periods: true,
      },
    });
  });

  it("Should generate documents", async () => {
    const claim = ClaimGenerator.generate(employeePool, {}, medical);
    expect(generateDocuments).toHaveBeenCalledWith(claim.claim, medical.docs);
  });

  function extractNotificationDate(claim: GeneratedClaim["claim"]): Date {
    const str = claim.leave_details?.employer_notification_date;
    if (!str) {
      throw new Error("No notification date given");
    }
    return new Date(str);
  }

  // it("Should have an application start date past 01/01/2021", async () => {
  //   // We run through this test 100 times, because we're dealing with randomness
  //   // and need to be sure we're always getting a valid result.
  //   for (let i = 0; i < 100; i++) {
  //     const claim = await scenario("TEST", medical)(opts);
  //     const period = claim.claim.leave_details?.continuous_leave_periods?.[0];
  //     if (period === null || period === undefined) {
  //       throw new Error("No period was present on the claim");
  //     }
  //     expect(period?.start_date).toMatch(/^2021\-/);
  //   }
  // });

  it("Should have an application end date greater/later than start date", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, medical);
    const [start, end] = extractLeavePeriod(claim);
    expect(start.getTime()).toBeLessThan(end.getTime());
  });

  it("Should allow for a short leave period to be generated", async () => {
    const { claim } = ClaimGenerator.generate(
      employeePool,
      {},
      { ...medical, shortClaim: true }
    );
    const [start, end] = extractLeavePeriod(claim);
    // End - start should = 7 days worth of seconds.
    expect(end.getTime() - start.getTime()).toEqual(24 * 60 * 60 * 1000);
  });

  // it("Should allow for arbitrary scenario configuration to be overridden by options", async () => {
  //   const { claim } = await scenario(
  //     "TEST",
  //     medical
  //   )({ ...opts, shortClaim: true });
  //   const [start, end] = extractLeavePeriod(claim);
  //   // End - start should = 7 days worth of seconds.
  //   expect(end.getTime() - start.getTime()).toEqual(24 * 60 * 60 * 1000);
  // });

  it("Should have an application end date within 20 weeks of the start date", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, medical);
    const [start, end] = extractLeavePeriod(claim);
    expect(end.getTime() - start.getTime()).toBeLessThan(
      // 20 weeks worth of milliseconds...
      86400 * 1000 * 7 * 20
    );
  });

  it("Should have a notification date prior to the leave start date", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, medical);
    const [start] = extractLeavePeriod(claim);
    const notification = extractNotificationDate(claim);

    expect(notification.getTime()).toBeLessThan(start.getTime());
  });

  // @todo: I carried this test over, but I'm not sure what the purpose is.
  it("Should have a notification date that qualifies as short notice", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, medical);
    const [start] = extractLeavePeriod(claim);
    const notification = extractNotificationDate(claim);
    expect(notification.getTime()).toBeLessThanOrEqual(
      start.getTime() - 86400 * 1000
    );
  });

  it("Should set the leave reason for medical claims", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim.leave_details).toMatchObject({
      reason: medical.reason,
      reason_qualifier: medical.reason_qualifier,
    });
  });

  it("Should set the leave reason for bonding claims", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, bonding);
    expect(claim.leave_details).toMatchObject({
      reason: bonding.reason,
      reason_qualifier: bonding.reason_qualifier,
    });
  });

  it("Should set the child birth date for bonding newborn claims", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, bonding);
    expect(claim.leave_details?.child_birth_date).toMatch(/\d{4}-\d{2}-\d{2}/);
  });
  it("Should set the child placement date for bonding adoption claims", async () => {
    const { claim } = ClaimGenerator.generate(
      employeePool,
      {},
      { ...bonding, reason_qualifier: "Adoption" }
    );
    expect(claim.leave_details?.child_placement_date).toMatch(
      /\d{4}-\d{2}-\d{2}/
    );
  });
  it("Should set the child placement date for bonding foster claims", async () => {
    const { claim } = ClaimGenerator.generate(
      employeePool,
      {},
      { ...bonding, reason_qualifier: "Foster Care" }
    );
    expect(claim.leave_details?.child_placement_date).toMatch(
      /\d{4}-\d{2}-\d{2}/
    );
  });

  it("Should create a reduced leave claim", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, reduced);
    const [start, end] = extractLeavePeriod(
      claim,
      "reduced_schedule_leave_periods"
    );
    expect(start.getTime()).toBeLessThan(end.getTime());
    expect(claim.leave_details?.reduced_schedule_leave_periods).toEqual([
      expect.objectContaining({
        sunday_off_minutes: 0,
        monday_off_minutes: 240,
        tuesday_off_minutes: 240,
        wednesday_off_minutes: 240,
        thursday_off_minutes: 240,
        friday_off_minutes: 240,
        saturday_off_minutes: 0,
      }),
    ]);
  });

  it("Should create a reduced leave claim for a rotating shift pattern", async () => {
    const { claim } = ClaimGenerator.generate(
      employeePool,
      {},
      {
        ...reduced,
        work_pattern_spec: "0,720,720",
        reduced_leave_spec: "0,240,240",
      }
    );
    const [start, end] = extractLeavePeriod(
      claim,
      "reduced_schedule_leave_periods"
    );
    expect(start.getTime()).toBeLessThan(end.getTime());
    expect(claim.leave_details?.reduced_schedule_leave_periods).toEqual([
      expect.objectContaining({
        sunday_off_minutes: 0,
        monday_off_minutes: 240,
        tuesday_off_minutes: 240,
        wednesday_off_minutes: 0,
        thursday_off_minutes: 0,
        friday_off_minutes: 0,
        saturday_off_minutes: 0,
      }),
    ]);
  });

  it("Should create a claim with a rotating schedule", async () => {
    const { claim } = ClaimGenerator.generate(
      employeePool,
      {},
      {
        ...medical,
        work_pattern_spec: "rotating_shift",
      }
    );
    expect(claim.work_pattern).toEqual({
      work_pattern_type: "Rotating",
      work_week_starts: "Monday",
      work_pattern_days: [
        { day_of_week: "Sunday", minutes: 0, week_number: 1 },
        { day_of_week: "Monday", minutes: 720, week_number: 1 },
        { day_of_week: "Tuesday", minutes: 0, week_number: 1 },
        { day_of_week: "Wednesday", minutes: 720, week_number: 1 },
        { day_of_week: "Thursday", minutes: 0, week_number: 1 },
        { day_of_week: "Friday", minutes: 720, week_number: 1 },
        { day_of_week: "Saturday", minutes: 0, week_number: 1 },
        { day_of_week: "Sunday", minutes: 720, week_number: 2 },
        { day_of_week: "Monday", minutes: 0, week_number: 2 },
        { day_of_week: "Tuesday", minutes: 720, week_number: 2 },
        { day_of_week: "Wednesday", minutes: 0, week_number: 2 },
        { day_of_week: "Thursday", minutes: 720, week_number: 2 },
        { day_of_week: "Friday", minutes: 0, week_number: 2 },
        { day_of_week: "Saturday", minutes: 0, week_number: 2 },
      ],
    });
  });

  it("Should create an intermittent leave claim", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, intermittent);
    const [start, end] = extractLeavePeriod(
      claim,
      "intermittent_leave_periods"
    );
    expect(start.getTime()).toBeLessThan(end.getTime());
  });

  it("Should not set pregnant_or_given_birth unless requested to do so", async () => {
    const { claim } = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim).toMatchObject({
      leave_details: expect.objectContaining({
        pregnant_or_recent_birth: false,
      }),
    });
  });

  it("Should allow for medical pre-birth claims to be created", async () => {
    const { claim } = ClaimGenerator.generate(
      employeePool,
      {},
      {
        ...medical,
        pregnant_or_recent_birth: true,
      }
    );
    expect(claim).toMatchObject({
      leave_details: expect.objectContaining({
        pregnant_or_recent_birth: true,
      }),
    });
  });

  it("Should not add employer response by default", async () => {
    const claim = ClaimGenerator.generate(employeePool, {}, medical);
    expect(claim.employerResponse).toBe(null);
  });

  it("Should support adding an employer response", async () => {
    const employerResponse = {
      hours_worked_per_week: 40,
      fraud: "No" as const,
      employer_decision: "Approve" as const,
      comment: "Test test",
    };
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      { ...medical, employerResponse }
    );
    expect(claim.employerResponse).toEqual({
      ...employerResponse,
      employer_benefits: [],
      previous_leaves: [],
    });
  });

  it("Should support generating previous_leaves on employer response", async () => {
    const employerResponse = {
      hours_worked_per_week: 40,
      fraud: "No" as const,
      employer_decision: "Approve" as const,
      comment: "Test test",
      previous_leaves: [previousLeaveWithoutDates, previousLeave],
    };
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      { ...medical, employerResponse }
    );
    expect(claim.employerResponse?.previous_leaves).toHaveLength(2);
    claim.employerResponse?.previous_leaves.forEach((previous_leave) => {
      expect(previous_leave).toMatchObject({
        leave_start_date: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
        leave_end_date: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
      });
    });
  });

  it("Should support generating employer_benefits on employer response", async () => {
    const employerResponse = {
      hours_worked_per_week: 40,
      fraud: "No" as const,
      employer_decision: "Approve" as const,
      comment: "Test test",
      employer_benefits: [benefitWithExplicitDates, benefitWithoutDates],
    };
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      { ...medical, employerResponse }
    );
    expect(claim.employerResponse?.employer_benefits).toHaveLength(2);
    claim.employerResponse?.employer_benefits.forEach((benefit) => {
      expect(benefit).toMatchObject({
        benefit_start_date: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
        benefit_end_date: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
      });
    });
  });

  it("Should support generating concurrent_leave on employer response", () => {
    const employerResponse: EmployerResponseSpec = {
      hours_worked_per_week: 40,
      fraud: "No",
      employer_decision: "Approve",
      comment: "Test test",
      concurrent_leave: { is_for_current_employer: true },
    };
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      { ...medical, employerResponse }
    );
    expect(claim.employerResponse?.concurrent_leave).toMatchObject({
      is_for_current_employer: true,
      leave_start_date: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
      leave_end_date: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
    });
  });

  it("Should use the provided field data", async () => {
    const claim = ClaimGenerator.generate(employeePool, {}, payments);
    expect(claim.claim.mailing_address).toMatchObject({
      city: "City",
      line_1: "123 Street Road",
      state: "MA",
      zip: "00000",
    });
    expect(claim.claim.residential_address).toMatchObject({
      city: "City",
      line_1: "123 Street Road",
      state: "MA",
      zip: "00000",
    });
    expect(claim.claim.leave_details).toMatchObject({
      continuous_leave_periods: [
        {
          start_date: "2021-01-01",
          end_date: "2021-02-01",
        },
      ],
    });
    expect(claim.paymentPreference.payment_preference).toMatchObject({
      payment_method: "Check",
      account_number: "",
      routing_number: "",
      bank_account_type: "Checking",
    });
  });

  it("should use exlicit leave dates when generating a reduced leave claim", async () => {
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      reduced_explicit_dates
    );
    const start =
      claim.claim.leave_details?.reduced_schedule_leave_periods?.[0]
        ?.start_date;
    const end =
      claim.claim.leave_details?.reduced_schedule_leave_periods?.[0]?.end_date;

    expect(start).toEqual(START_LEAVE);
    expect(end).toEqual(END_LEAVE);
  });

  it("should use explicit leave dates when generating an intermittent leave claim", async () => {
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      intermittent_explicit_dates
    );
    const start =
      claim.claim.leave_details?.intermittent_leave_periods?.[0]?.start_date;
    const end =
      claim.claim.leave_details?.intermittent_leave_periods?.[0]?.end_date;

    expect(start).toEqual(START_LEAVE);
    expect(end).toEqual(END_LEAVE);
  });

  describe("Other leaves & benefits", () => {
    describe("Previous leaves", () => {
      it("Should set the previous leave dates if given a previous_leaves_other_reason with unspecified dates", () => {
        // Setup
        const claim_spec: ClaimSpecification = {
          ...intermittent_explicit_dates,
          previous_leaves_other_reason: [previousLeaveWithoutDates],
        };
        const { claim } = ClaimGenerator.generate(employeePool, {}, claim_spec);
        // Get rid of null checks
        assertIsTypedArray(
          claim.previous_leaves_other_reason,
          isValidPreviousLeave
        );
        // Expect dates to be added.
        expect(claim.previous_leaves_other_reason).toEqual([
          {
            ...previousLeaveWithoutDates,
            leave_start_date: expect.any(String),
            leave_end_date: expect.any(String),
          },
        ]);
        // Expect previous leave dates to be before current leave dates
        expect(
          parseISO(claim.previous_leaves_other_reason[0].leave_end_date) <
            parseISO(START_LEAVE)
        ).toBe(true);
        // Expect previous leave start date to be before it's end date
        expect(
          parseISO(claim.previous_leaves_other_reason[0].leave_start_date) <
            parseISO(claim.previous_leaves_other_reason[0].leave_end_date)
        ).toBe(true);
        expect(claim.has_previous_leaves_other_reason).toBe(true);
      });
      it("Should pass through the previous leave spec if given a previous_leaves_same_reason without specified dates", () => {
        // Setup
        const claim_spec: ClaimSpecification = {
          ...intermittent_explicit_dates,
          previous_leaves_same_reason: [previousLeave],
        };
        const { claim } = ClaimGenerator.generate(employeePool, {}, claim_spec);
        // Check that the spec is passed
        expect(claim.previous_leaves_same_reason).toEqual([previousLeave]);
        expect(claim.has_previous_leaves_same_reason).toBe(true);
      });
    });
    it("Can specify other benefits in the claim spec", () => {
      // Setup
      const claim_spec: ClaimSpecification = {
        ...intermittent_explicit_dates,
        employer_benefits: [benefitWithExplicitDates, benefitWithoutDates],
      };
      const { claim } = ClaimGenerator.generate(employeePool, {}, claim_spec);

      // Check spec is passed and dates are generated.
      expect(claim.employer_benefits).toEqual([
        benefitWithExplicitDates,
        {
          ...benefitWithoutDates,
          benefit_start_date: START_LEAVE,
          benefit_end_date: END_LEAVE,
        },
      ]);
      expect(claim.has_employer_benefits).toBe(true);
    });
    it("Can specify other incomes in the claim spec", () => {
      // Setup
      const claim_spec: ClaimSpecification = {
        ...intermittent_explicit_dates,
        other_incomes: [otherIncomeWithDates, otherIncomeWithoutDates],
      };
      const { claim } = ClaimGenerator.generate(employeePool, {}, claim_spec);
      // Check spec is passed and dates are generated.
      expect(claim.other_incomes).toEqual([
        otherIncomeWithDates,
        {
          ...otherIncomeWithoutDates,
          income_start_date: START_LEAVE,
          income_end_date: END_LEAVE,
        },
      ]);
      expect(claim.has_other_incomes).toBe(true);
    });
    // Concurrent leave test for specs with and wthout dates are essentially the same
    const concurrentLeaveTable = [
      [
        "dates",
        { is_for_current_employer: true },
        {
          is_for_current_employer: true,
          leave_end_date: END_LEAVE,
          leave_start_date: START_LEAVE,
        },
      ],
      [
        "no dates",
        {
          is_for_current_employer: true,
          leave_end_date: "2021-01-02",
          leave_start_date: "2021-01-02",
        },
        {
          is_for_current_employer: true,
          leave_end_date: "2021-01-02",
          leave_start_date: "2021-01-02",
        },
      ],
    ];
    it.each(concurrentLeaveTable)(
      "Should generate a concurrent leave if given % the spec",
      (_, given, expected) => {
        const claim_spec: ClaimSpecification = {
          ...intermittent_explicit_dates,
          concurrent_leave: given,
        };
        const { claim } = ClaimGenerator.generate(employeePool, {}, claim_spec);
        expect(claim.concurrent_leave).toEqual(expected);
        expect(claim.has_concurrent_leave).toBe(true);
      }
    );
  });

  it("Should allow passing in configuration for an intermittent leave period", async () => {
    const claim = ClaimGenerator.generate(
      employeePool,
      {},
      {
        ...intermittent,
        intermittent_leave_spec: { duration: 1, duration_basis: "Hours" },
      }
    );
    expect(
      claim.claim.leave_details?.intermittent_leave_periods?.[0].duration
    ).toEqual(1);
    expect(
      claim.claim.leave_details?.intermittent_leave_periods?.[0].duration_basis
    ).toEqual("Hours");

    const claim2 = ClaimGenerator.generate(
      employeePool,
      {},
      {
        ...intermittent,
        intermittent_leave_spec: [{ duration: 1, duration_basis: "Hours" }],
      }
    );
    expect(
      claim2.claim.leave_details?.intermittent_leave_periods?.[0].duration
    ).toEqual(1);
    expect(
      claim2.claim.leave_details?.intermittent_leave_periods?.[0].duration_basis
    ).toEqual("Hours");
  });
});

describe("ClaimPool", () => {
  let tempDir: string;

  let employeePool: EmployeePool;
  beforeEach(() => {
    jest.clearAllMocks();
    employeePool = new EmployeePool([employee]);
    mocked(employeePool).pick.mockImplementation(() => employee);
    generateDocumentsMock.mockImplementation(() => {
      return [
        {
          document_type: "Identification Proof",
          file: () =>
            Promise.resolve(
              new Uint8ArrayWrapper(Buffer.from("test"), "test.pdf")
            ),
        },
      ];
    });
  });

  beforeAll(async () => {
    tempDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "documents"));
  });

  afterAll(async () => {
    if (tempDir) {
      await fs.promises.rmdir(tempDir);
    }
  });

  const collect = async function <T extends unknown>(
    iter: AsyncIterable<T>
  ): Promise<T[]> {
    const items = [];
    for await (const item of iter) {
      items.push(item);
    }
    return items;
  };

  it("Should generate claims", async () => {
    const pool = ClaimPool.generate(employeePool, {}, medical, 5);
    const collected = await collect(pool);
    expect(collected).toHaveLength(5);
  });

  it("Should be saveable and loadable", async () => {
    const file = path.join(tempDir, "claims.ndjson");
    const expected = await collect(
      ClaimPool.generate(employeePool, {}, medical, 1)
    );

    await new ClaimPool(expected).save(file, tempDir);
    const actual = await collect(await ClaimPool.load(file, tempDir));

    // Compare everything except for the documents, which are not directly comparable.
    const expectedComparable = expected.map(({ documents, ...rest }) => rest);
    const actualComparable = actual.map(({ documents, ...rest }) => rest);
    expect(actualComparable).toEqual(expectedComparable);

    // Collect all the documents for a given claim, extracting the text into the file property. This allows us to
    // do equality comparisons on the file contents.
    const collectDocs = ({ documents }: GeneratedClaim) =>
      Promise.all(
        documents.map(async (doc) => ({
          ...doc,
          file: await doc.file().then(async (f) => {
            return Buffer.from(await collect(f.asStream())).toString("utf-8");
          }),
        }))
      );
    // Extract docs from expected and actual claims, then compare them.
    const expectedDocs = await Promise.all(expected.map(collectDocs));
    const actualDocs = await Promise.all(actual.map(collectDocs));
    expect(actualDocs).toEqual(expectedDocs);
  });

  it("Should throw an error if requested to open a nonexistent file", async () => {
    const file = path.join(tempDir, "claims-nonexistent.ndjson");
    expect(
      async () => await ClaimPool.load(file, tempDir)
    ).rejects.toThrowError("ENOENT");
  });

  describe("orGenerateAndSave", () => {
    beforeEach(async () => {
      await prepareStorage();
    });
    afterEach(async () => {
      await removeStorage();
    });
    it("orGenerateAndSave() will claims to hard drive", async () => {
      const claims = ClaimPool.generate(employeePool, {}, medical, 1);
      const gen = jest.fn(() => claims);
      await ClaimPool.load(storage.claims, storage.documents).orGenerateAndSave(
        gen
      );
      const refreshedPool = await collect(
        await ClaimPool.load(storage.claims, storage.documents)
      );
      expect(gen).toHaveBeenCalled();
      expect(refreshedPool.length).toBe(1);
    });

    it("orGenerateAndSave() will generate used employees when used with load()", async () => {
      const pool = await collect(
        await ClaimPool.load(
          storage.claims,
          storage.documents
        ).orGenerateAndSave(() =>
          ClaimPool.generate(employeePool, {}, medical, 1)
        )
      );
      expect(pool.length).toBe(1);
    });

    it("Should generate proper leave dates for caring leave claims", () => {
      const { claim } = ClaimGenerator.generate(
        employeePool,
        {},
        caring_leave_dates
      );
      const [start, end] = extractLeavePeriod(claim);
      const leave_period_weeks = differenceInCalendarWeeks(end, start);
      expect(isSunday(start)).toBe(true);
      expect(isAfter(start, parseISO("2021-07-01"))).toBe(true);
      expect(leave_period_weeks).toEqual(2);
    });
  });
});
