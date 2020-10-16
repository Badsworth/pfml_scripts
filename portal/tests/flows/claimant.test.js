import Claim, {
  ClaimStatus,
  EmploymentStatus,
  LeaveReason,
} from "../../src/models/Claim";
import { Machine, assign } from "xstate";
import claimFlowStates, { guards } from "../../src/flows/claimant";
import { get, merge } from "lodash";
import User from "../../src/models/User";
import { createModel } from "@xstate/test";
import machineConfigs from "../../src/flows";
import routes from "../../src/routes";

// In order to determine level of test coverage, each route
// needs a test function defined for meta
const machineTests = {
  [routes.claims.dashboard]: {
    meta: {
      test: () => {},
    },
    // When exiting dashboard state,
    // add test data to the machine's context
    exit: "assignTestDataToMachineContext",
  },
  [routes.user.consentToDataSharing]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.checklist]: {
    meta: {
      test: () => {},
    },
  },
  [routes.applications]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.start]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.success]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.name]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.address]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.dateOfBirth]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.stateId]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.uploadId]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.ssn]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.leaveReason]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.reasonPregnancy]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "leave_details.reason")).toEqual(
          LeaveReason.medical
        );
      },
    },
  },
  [routes.claims.uploadCertification]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.dateOfChild]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "leave_details.reason")).toEqual(
          LeaveReason.bonding
        );
      },
    },
  },
  [routes.claims.leavePeriodContinuous]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.leavePeriodReducedSchedule]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.leavePeriodIntermittent]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.intermittentFrequency]: {
    meta: {
      test: (_, event) => {
        expect(
          get(event.context.claim, "has_intermittent_leave_periods")
        ).toEqual(true);
      },
    },
  },
  [routes.claims.employerBenefits]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.employerBenefitDetails]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "temp.has_employer_benefits")).toEqual(
          true
        );
      },
    },
  },
  [routes.claims.otherIncomes]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.otherIncomesDetails]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "temp.has_other_incomes")).toEqual(
          true
        );
      },
    },
  },
  [routes.claims.previousLeaves]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.previousLeavesDetails]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "temp.has_previous_leaves")).toEqual(
          true
        );
      },
    },
  },
  [routes.claims.employmentStatus]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.hoursWorkedPerWeek]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.notifiedEmployer]: {
    meta: {
      test: (_, event) => {
        expect(get(event.context.claim, "employment_status")).toEqual(
          EmploymentStatus.employed
        );
      },
    },
  },
  [routes.claims.paymentMethod]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.review]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.uploadDocsOptions]: {
    meta: {
      test: () => {},
    },
  },
};

const machineConfigsWithTests = {
  ...machineConfigs,
  states: merge(claimFlowStates.states, machineTests),
};

describe("claimFlowConfigs", () => {
  const context = {
    claim: new Claim({ application_id: "mock-application-id" }),
    user: new User({ user_id: "mock-user-id" }),
  };

  // Define various states a claim can be in that will result in
  // different routing paths
  const medicalClaim = { leave_details: { reason: LeaveReason.medical } };
  const bondingClaim = { leave_details: { reason: LeaveReason.bonding } };
  const employed = {
    employment_status: EmploymentStatus.employed,
  };
  const hasEmployerBenefits = { temp: { has_employer_benefits: true } };
  const hasIntermittentLeavePeriods = { has_intermittent_leave_periods: true };
  const hasOtherIncomes = { temp: { has_other_incomes: true } };
  const hasStateId = { has_state_id: true };
  const hasPreviousLeaves = { temp: { has_previous_leaves: true } };
  const completed = {
    status: ClaimStatus.completed,
  };
  const testData = [
    { claimData: hasStateId, userData: {} },
    { claimData: medicalClaim, userData: {} },
    { claimData: employed, userData: {} },
    { claimData: hasEmployerBenefits, userData: {} },
    { claimData: hasIntermittentLeavePeriods, userData: {} },
    { claimData: hasOtherIncomes, userData: {} },
    { claimData: hasPreviousLeaves, userData: {} },
    { claimData: bondingClaim, userData: {} },
    { claimData: completed, userData: {} },
  ];

  // Action that's fired when exiting dashboard state and creating a claim and
  // adds test data to the current machine context
  const assignTestDataToMachineContext = assign({
    claim: (ctx, event) => new Claim({ ...ctx.claim, ...event.claimData }),
    user: (ctx, event) => new User({ ...ctx.user, ...event.userData }),
  });

  const routingMachine = Machine(
    {
      ...machineConfigsWithTests,
      context,
      initial: routes.claims.dashboard,
    },
    {
      guards,
      actions: { assignTestDataToMachineContext },
    }
  );

  // Create a model that simulates the routing behavior
  // of the portal application when tested.
  const testModel = createModel(routingMachine).withEvents({
    CONSENT_TO_DATA_SHARING: {},
    CONTINUE: {},
    CREATE_CLAIM: {},
    EMPLOYER_INFORMATION: {},
    LEAVE_DETAILS: {},
    OTHER_LEAVE: {},
    PAYMENT: {},
    REVIEW_AND_CONFIRM: {},
    START: { cases: testData },
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
