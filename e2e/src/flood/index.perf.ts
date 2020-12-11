import {
  StepFunction,
  TestSettings,
  Browser,
  beforeEach,
  TestData,
  step,
} from "@flood/element";
import {
  globalElementSettings,
  dataBaseUrl,
  LSTScenario,
  LSTSimClaim,
} from "./config";
import scenarios from "./scenarios";

export const settings: TestSettings = {
  ...globalElementSettings,
  // These overrides are essential to any Flood.io deployment
  loopCount: -1,
  actionDelay: 1,
  stepDelay: 1,
};

export default (): void => {
  // Define variable that will control which scenario we're going to execute here.
  let curr: LSTScenario;
  // Set up test data to control execution.
  TestData.fromJSON<LSTSimClaim>(`./${dataBaseUrl}/claims.json`)
    .shuffle(true)
    .circular(true);
  // Before moving on to next scenario, fetch and adjust data needed
  beforeEach(async (browser: Browser, data?: LSTSimClaim) => {
    if (typeof data !== "object" || !data || !("scenario" in data)) {
      throw new Error("Unable to determine scenario for step");
    }
    curr = data.scenario;
    if (!Object.keys(scenarios).includes(curr)) {
      throw new Error(`Unknown step requested: ${curr}`);
    }
  });
  // Loops through all scenarios and defines the steps for each.
  Object.entries(scenarios).forEach(([scenario, steps]) => {
    steps.forEach((stepDef) => {
      step.if(
        () => curr === scenario,
        `${scenario}: ${stepDef.name}`,
        stepDef.test as StepFunction<unknown>
      );
    });
  });
};
