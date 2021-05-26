import BenefitsApplication, {
  BenefitsApplicationStatus,
  EmploymentStatus,
  WorkPatternType,
} from "../../src/models/BenefitsApplication";
import { Machine, assign } from "xstate";
import claimFlowStates, { guards } from "../../src/flows/claimant";
import { get, merge } from "lodash";
import LeaveReason from "../../src/models/LeaveReason";
import User from "../../src/models/User";
import { createModel } from "@xstate/test";
import machineConfigs from "../../src/flows";
import routes from "../../src/routes";

// In order to determine level of test coverage, each route
// needs a test function defined for meta
const machineTests = {
  [routes.applications.getReady]: {
    meta: {
      test: () => {},
    },
    // When exiting getReady state,
    // add test data to the machine's context
    exit: "assignTestDataToMachineContext",
  },
  [routes.user.consentToDataSharing]: {
    meta: {
      test: () => {},
    },
  },
  [routes.user.convert]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.checklist]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.index]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.start]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.success]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.name]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.phoneNumber]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.address]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.dateOfBirth]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.stateId]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.uploadId]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.ssn]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.leaveReason]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.reasonPregnancy]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "leave_details.reason")).toEqual(
          LeaveReason.medical
        );
      },
    },
  },
  [routes.applications.uploadCertification]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.dateOfChild]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "leave_details.reason")).toEqual(
          LeaveReason.bonding
        );
      },
    },
  },
  [routes.applications.leavePeriodContinuous]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.leavePeriodReducedSchedule]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.leavePeriodIntermittent]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.intermittentFrequency]: {
    meta: {
      test: (_, event) => {
        expect(
          get(event.context.claim, "has_intermittent_leave_periods")
        ).toEqual(true);
      },
    },
  },
  [routes.applications.employerBenefitsIntro]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.employerBenefits]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.employerBenefitsDetails]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "has_employer_benefits")).toEqual(true);
      },
    },
  },
  [routes.applications.otherIncomes]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.otherIncomesDetails]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "has_other_incomes")).toEqual(true);
      },
    },
  },
  [routes.applications.previousLeavesIntro]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.previousLeavesSameReason]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.previousLeavesSameReasonDetails]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.previousLeavesOtherReason]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.previousLeavesOtherReasonDetails]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.concurrentLeavesIntro]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.concurrentLeaves]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.concurrentLeavesDetails]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.employmentStatus]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.notifiedEmployer]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "employment_status")).toEqual(
          EmploymentStatus.employed
        );
      },
    },
  },
  [routes.applications.paymentMethod]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.bondingLeaveAttestation]: {
    meta: {
      test: (_, event) => {
        expect(event.context.claim.isBondingLeave).toEqual(true);
      },
    },
  },
  [routes.applications.reducedLeaveSchedule]: {
    meta: {
      test: (_, event) => {
        expect(
          get(event.context.claim, "has_reduced_schedule_leave_periods")
        ).toEqual(true);
      },
    },
  },
  [routes.applications.review]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.uploadDocsOptions]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.workPatternType]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications.scheduleFixed]: {
    meta: {
      test: (_, event) => {
        expect(
          get(event.context.claim, "work_pattern.work_pattern_type")
        ).toEqual(WorkPatternType.fixed);
      },
    },
  },
  [routes.applications.scheduleVariable]: {
    meta: {
      test: (_, event) => {
        expect(
          get(event.context.claim, "work_pattern.work_pattern_type")
        ).toEqual(WorkPatternType.variable);
      },
    },
  },
  [routes.applications.caringLeaveAttestation]: {
    meta: {
      test: (_, event) => {
        expect(event.context.claim.isCaringLeave).toEqual(true);
      },
    },
  },
  [routes.applications.familyMemberDateOfBirth]: {
    meta: {
      test: (_, event) => {
        expect(event.context.claim.isCaringLeave).toEqual(true);
      },
    },
  },
  [routes.applications.familyMemberName]: {
    meta: {
      test: (_, event) => {
        expect(event.context.claim.isCaringLeave).toEqual(true);
      },
    },
  },
  [routes.applications.familyMemberRelationship]: {
    meta: {
      test: (_, event) => {
        expect(event.context.claim.isCaringLeave).toEqual(true);
      },
    },
  },
};

const machineConfigsWithTests = {
  ...machineConfigs,
  states: merge(claimFlowStates.states, machineTests),
};

describe("claimFlowConfigs", () => {
  const context = {
    claim: new BenefitsApplication({ application_id: "mock-application-id" }),
    user: new User({ user_id: "mock-user-id" }),
  };

  // Define various states a claim can be in that will result in
  // different routing paths
  const medicalClaim = { leave_details: { reason: LeaveReason.medical } };
  const bondingClaim = { leave_details: { reason: LeaveReason.bonding } };
  const caringLeaveClaim = { leave_details: { reason: LeaveReason.care } };
  const employed = {
    employment_status: EmploymentStatus.employed,
  };
  const hasIntermittentLeavePeriods = { has_intermittent_leave_periods: true };
  const hasReducedScheduleLeavePeriods = {
    has_reduced_schedule_leave_periods: true,
  };
  const hasOtherLeavesAndIncomes = {
    has_employer_benefits: true,
    has_other_incomes: true,
    has_previous_leaves_other_reason: true,
    has_previous_leaves_same_reason: true,
  };
  const hasStateId = { has_state_id: true };
  const fixedWorkPattern = {
    work_pattern: { work_pattern_type: WorkPatternType.fixed },
  };
  const variableWorkPattern = {
    work_pattern: { work_pattern_type: WorkPatternType.variable },
  };
  const completed = {
    status: BenefitsApplicationStatus.completed,
  };
  const testData = [
    { claimData: hasStateId, userData: {} },
    { claimData: medicalClaim, userData: {} },
    { claimData: employed, userData: {} },
    { claimData: hasIntermittentLeavePeriods, userData: {} },
    { claimData: hasReducedScheduleLeavePeriods, userData: {} },
    { claimData: hasOtherLeavesAndIncomes, userData: {} },
    { claimData: bondingClaim, userData: {} },
    { claimData: completed, userData: {} },
    { claimData: fixedWorkPattern, userData: {} },
    { claimData: variableWorkPattern, userData: {} },
    { claimData: caringLeaveClaim, userData: {} },
  ];

  // Action that's fired when exiting getReady state and creating a claim and
  // adds test data to the current machine context
  const assignTestDataToMachineContext = assign({
    claim: (ctx, event) =>
      new BenefitsApplication({ ...ctx.claim, ...event.claimData }),
    user: (ctx, event) => new User({ ...ctx.user, ...event.userData }),
  });

  const routingMachine = Machine(
    {
      ...machineConfigsWithTests,
      context,
      initial: routes.applications.getReady,
    },
    {
      guards: {
        ...guards,
        // TODO (CP-1447): Remove this guard once the feature flag is obsolete
        showPhone: () => true,
      },
      actions: { assignTestDataToMachineContext },
    }
  );

  // Create a model that simulates the routing behavior
  // of the portal application when tested.
  const testModel = createModel(routingMachine).withEvents({
    CONSENT_TO_DATA_SHARING: {},
    PREVENT_CONVERSION: {},
    CONVERT_EMPLOYER: {},
    CONTINUE: {},
    CREATE_CLAIM: {},
    EMPLOYER_INFORMATION: {},
    LEAVE_DETAILS: {},
    OTHER_LEAVE: {},
    PAYMENT: {},
    REVIEW_AND_CONFIRM: {},
    SHOW_APPLICATIONS: {},
    START_APPLICATION: { cases: testData },
    UPLOAD_CERTIFICATION: {},
    UPLOAD_DOCS: {},
    UPLOAD_ID: {},
    UPLOAD_MASS_ID: {},
    VERIFY_ID: {},
  });

  // A testing plan represents a single routing path.
  // Generate the shortest paths to all routes based
  // on available transitions.
  const testPlans = testModel.getShortestPathPlans();

  testPlans.forEach((plan) => {
    describe(plan.description, () => {
      plan.paths.forEach((path) => {
        /* eslint-disable jest/expect-expect */
        it(path.description, async () => {
          // Here is where we can simulate our application's environment
          // and pass it to our test
          // e.g if using for e2e testing
          // > await page.goto(path.state.value)
          // > await path.test(page)
          // and within the machineTests `test` method, add assertions for
          // that page
          await path.test();
        });
        /* eslint-enable jest/expect-expect */
      });
    });
  });

  /* eslint-disable jest/expect-expect */
  it("should have full coverage", () => {
    // test that all routes `test` methods were evaluated at least once
    return testModel.testCoverage();
  });
  /* eslint-enable jest/expect-expect */
});
