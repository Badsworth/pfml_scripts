import {
  TestSettings,
  TestData,
  Browser,
  beforeEach,
  step,
} from "@flood/element";
import { StoredStep } from "./config";
import { SimulationClaim } from "../simulation/types";
import * as Fineos from "./tests/FineosClaimSubmit.perf";
import * as PortalSubmit from "./tests/PortalClaimSubmit.perf";
import * as PortalRegistration from "./tests/PortalRegistration.perf";
import * as SavilinxAgent from "./tests/SavilinxAgent.perf";

export const settings: TestSettings = {
  loopCount: 50,
  actionDelay: 1,
  stepDelay: 1,
  waitUntil: "visible",
  name: "PFML Load Test Bot",
  userAgent: "PFML Load Test Bot",
  description: "PFML Load Test Bot",
  screenshotOnFailure: true,
  disableCache: true,
  clearCache: true,
  clearCookies: true,
};

type ScenarioMap = {
  [k: string]: StoredStep[];
};

// List of imported scenarios to execute
// Essentially all scenario imported files
const availableScenarios = [
  Fineos,
  PortalSubmit,
  PortalRegistration,
  SavilinxAgent,
];

const scenarios: ScenarioMap = availableScenarios.reduce(
  (allScenarios, curr) => ({
    ...allScenarios,
    [curr.scenario]: curr.steps,
  }),
  {}
);

export default (): void => {
  // Define variable that will control which scenario we're going to execute here.
  let curr: string;

  // Set up test data to control execution.
  TestData.fromJSON<SimulationClaim>("./data/pilot3/claims.json");

  // Before moving on to next scenario, fetch and adjust data needed
  // @flood/element@1.3.5
  beforeEach(async (browser: Browser, data?: unknown) => {
    if (typeof data !== "object" || !data || !("scenario" in data)) {
      throw new Error("Unable to determine scenario for step");
    }
    curr = (data as SimulationClaim).scenario;
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
        stepDef.test
      );
    });
  });
};
