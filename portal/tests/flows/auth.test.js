import { Machine } from "xstate";
import authFlowStates from "../../src/flows/auth";
import { createModel } from "@xstate/test";
import machineConfigs from "../../src/flows";
import { merge } from "lodash";
import routes from "../../src/routes";

// routes.claims.dashboard is not a path in flow-confings/auth.js, but it's used in the CONTINUE for routes.auth.login, so it needs to be included in the list
const createAccountStates = [
  routes.auth.createAccount,
  routes.auth.verifyAccount,
  routes.auth.login,
  routes.claims.dashboard,
];

const forgotPasswordStates = [
  routes.auth.forgotPassword,
  routes.claims.dashboard,
  routes.auth.login,
  routes.auth.verifyAccount,
  routes.auth.resetPassword,
];

const machineTestGenerator = (states) => {
  const statesWithMeta = {};
  states.forEach((state) => {
    statesWithMeta[state] = { meta: { test: () => {} } };
  });
  return statesWithMeta;
};

const extractTestStatesFromAuthFlow = (states) => {
  // Pulls out the states that we want to test in a particular flow
  const testStates = {};
  states.forEach((state) => {
    if (state in authFlowStates.states) {
      testStates[state] = authFlowStates.states[state];
    }
  });
  return testStates;
};

const runTestsWithStatesAndEvents = (
  events,
  initial,
  machineConfigsWithTests
) => {
  const routingMachine = Machine({
    ...machineConfigsWithTests,
    context: {},
    initial,
  });

  // Create a model that simulates the routing behavior
  // of the portal application when tested.
  const testModel = createModel(routingMachine).withEvents(events);

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
};

describe("createAccountFlow", () => {
  // Test the state flow starting from createAccount
  const machineTests = machineTestGenerator(createAccountStates);
  const testStates = extractTestStatesFromAuthFlow(createAccountStates);

  const machineConfigsWithTests = {
    ...machineConfigs,
    states: merge(testStates, machineTests),
  };

  runTestsWithStatesAndEvents(
    {
      CREATE_ACCOUNT: {},
      LOG_IN: {},
      SUBMIT: {},
    },
    routes.auth.createAccount,
    machineConfigsWithTests
  );
});

describe("forgotPasswordFlow", () => {
  // Test the state flow starting from forgotPassword
  const machineTests = machineTestGenerator(forgotPasswordStates);
  const testStates = extractTestStatesFromAuthFlow(forgotPasswordStates);

  const machineConfigsWithTests = {
    ...machineConfigs,
    states: merge(testStates, machineTests),
  };

  runTestsWithStatesAndEvents(
    {
      UNCONFIRMED_ACCOUNT: {},
      LOG_IN: {},
      SEND_CODE: {},
      SET_NEW_PASSWORD: {},
    },
    routes.auth.forgotPassword,
    machineConfigsWithTests
  );
});
