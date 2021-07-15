import { Runnable, Test, Context } from "mocha";

/**
 * This file contains the dependsOnPreviousPass command.
 *
 * This command allows us to skip tests when a previous test in the suite fails. This is
 * necessary because we have tests that depend on each other. Eg: checking for notifications
 * depends on a claim being submitted, and it's pointless to spend time waiting for notifications
 * if the claim submission fails.
 *
 * To achieve this, we have to reach pretty deep into Cypress internals and track our own state.
 * In the future, we may be able to use the Mocha runnable's state instead of tracking it ourselves.
 * See https://github.com/mochajs/mocha/pull/4181, which is not available today (Cypress is currently
 * on an older Mocha version).
 */
// Track results on a global level.
const trackedResults: Record<string, Record<string, "passed" | "failed">> = {};

const getRunnableId = (runnable: Runnable): string => {
  // @ts-ignore
  return runnable.id;
};
const getRunnableSuiteId = (runnable: Runnable): string => {
  if (!runnable.parent) {
    throw new Error("Unable to get parent suite");
  }
  // @ts-ignore
  return runnable.parent.id;
};
function getMochaContext(): Context {
  // @ts-ignore "cy.state" is not in the "cy" type
  return cy.state("runnable").ctx;
}

Cypress.on("test:after:run", (attr, runnable) => {
  if (runnable.state) {
    const suiteId = getRunnableSuiteId(runnable);
    if (!trackedResults[suiteId]) {
      trackedResults[suiteId] = {};
    }
    trackedResults[suiteId][getRunnableId(runnable)] = runnable.state;
  }
});

type TestWithID = Test & { id: string };

Cypress.Commands.add("dependsOnPreviousPass", (dependencies?: [Test]) => {
  // @ts-ignore
  const runnable = cy.state("runnable") as Runnable;
  // When calculating whether this test's dependencies pass, only consider results
  // for the suite this test belongs to.
  const thisSuiteResults = trackedResults[getRunnableSuiteId(runnable)] ?? {};
  const thisTestId = getRunnableId(runnable);

  const dependentValues = Object.entries(thisSuiteResults).reduce(
    (results, [id, result]) => {
      // If we're viewing previous results for the current test, ignore it.
      if (id === thisTestId) {
        return results;
      }
      // If we weren't passed explicit dependencies, all previous tests are considered dependencies,
      // so consider them all.
      if (!dependencies) {
        return results.concat(result);
      }
      // If we were passed dependencies, only consider the result if it's one of our dependencies.
      if (dependencies.find((dep) => (dep as TestWithID).id === id)) {
        return results.concat(result);
      }
      // Otherwise, ignore this result.
      return results;
    },
    [] as ("passed" | "failed")[]
  );

  // If any of the previous results we're considering are not passes, we've failed
  // the check and should skip the current test.
  if (dependentValues.some((r) => r !== "passed")) {
    Cypress.runner.stop();
    getMochaContext().skip();
  }
});
