import { Machine } from "xstate";
import { createModel } from "@xstate/test";
import machineConfigs from "../../src/routes/claim-flow-configs";
import { merge } from "lodash";
import routes from "../../src/routes/index";

// in order to determine level of test coverage, each route
// needs a test function defined for meta
// we do not currently have any assertions that need to be made
const machineTests = {
  [routes.claims.checklist]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.name]: {
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
  [routes.claims.leaveDates]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.reasonPregnancy]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.duration]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.employmentStatus]: {
    meta: {
      test: () => {},
    },
  },
  [routes.claims.notifiedEmployer]: {
    meta: {
      test: () => {},
    },
  },
};

const machineConfigsWithTests = {
  ...machineConfigs,
  states: merge(machineConfigs.states, machineTests),
};

/**
 * @see https://xstate.js.org/docs/packages/xstate-test/#quick-start
 * comments below are based on current understanding of @xstate/test
 * and may need to be corrected
 */
describe("routingMachine", () => {
  const routingMachine = Machine({
    ...machineConfigsWithTests,
    initial: routes.claims.checklist,
  });

  // Create a model that simulates the routing behavior
  // of the portal application when tested.
  const testModel = createModel(routingMachine).withEvents({
    // provide additional context for transition events,
    // there are none currently
    CONTINUE: {},
    VERIFY_ID: {},
    LEAVE_DETAILS: {},
    EMPLOYER_INFORMATION: {},
    // TODO: remove once conditional routing for leaveReason exists
    TEMP_TEST_PREGNANCY_PATH: {},
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
    // test that all routes `test` methods were evaluted at least once
    return testModel.testCoverage();
  });
  /* eslint-enable jest/expect-expect */
});
