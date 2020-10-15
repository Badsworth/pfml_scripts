import { Machine } from "xstate";
import { createModel } from "@xstate/test";
import employerFlowStates from "../../src/flows/employer";
import machineConfigs from "../../src/flows";
import { merge } from "lodash";
import routes from "../../src/routes";

const verifyAccountStates = [
  routes.employers.finishAccountSetup,
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
    if (state in employerFlowStates.states) {
      testStates[state] = employerFlowStates.states[state];
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
};

describe("verifyAccountFlow", () => {
  const machineTests = machineTestGenerator(verifyAccountStates);
  const testStates = extractTestStatesFromAuthFlow(verifyAccountStates);

  const machineConfigsWithTests = {
    ...machineConfigs,
    states: merge(testStates, machineTests),
  };

  runTestsWithStatesAndEvents(
    {
      SEND_CODE: {},
    },
    routes.employers.finishAccountSetup,
    machineConfigsWithTests
  );
});
