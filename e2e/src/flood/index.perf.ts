import {
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
  actionDelay: 1, // needs to be 3 if running agents
  stepDelay: 1, // needs to be 8 if running agents
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
        async (browser: Browser, data: LSTSimClaim) => {
          try {
            await stepDef.test(browser, data);
          } catch (e) {
            // Catch and log failures so we can detect them in the logs.
            console.log(
              `\n\nDetected fatal failure while running ${curr}: ${stepDef.name}`,
              e,
              "\n\n"
            );
            await browser.takeScreenshot();
            throw e;
          }
        }
      );
    });
  });
};
