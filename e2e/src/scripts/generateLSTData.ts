import path from "path";
import * as JSONStream from "JSONStream";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline, Readable } from "stream";
import { merge, AnyIterable } from "streaming-iterables";
import dataDirectory from "../generation/DataDirectory";
import * as scenarios from "../scenarios";
import { ApplicationRequestBody } from "../api";
import { factory as EnvFactory } from "../config";
import EmployeePool from "../generation/Employee";
import ClaimPool, { GeneratedClaim } from "../generation/Claim";
import { LSTDataConfig } from "../commands/flood/common";
import EmployerPool, { Employer } from "../generation/Employer";

const pipelineP = promisify(pipeline);

/**
 * Generator function to generate Leave Admin scenarios.
 * @param employeePool
 * @param num
 */
function* generateLASRS(
  employerPool: EmployerPool,
  num: number
): Iterable<DummyScenarioObject & Employer> {
  for (let i = 0; i < num; i++) {
    yield {
      scenario: "LeaveAdminSelfRegistration",
      ...employerPool.pick(),
    };
  }
}

/**
 * Generator function to generate agent scenarios.
 * @param num
 */
function* generateAgents(num: number): Iterable<DummyScenarioObject> {
  for (let i = 0; i < num; i++) {
    yield {
      scenario: "SavilinxAgent",
    };
  }
}

type DummyScenarioObject = {
  scenario: string;
  claim?: {
    employer_fein: ApplicationRequestBody["employer_fein"];
  };
};

async function generateLSTData(
  env: string,
  dir: string,
  numRecords: number,
  data: LSTDataConfig[]
): Promise<boolean> {
  const config = EnvFactory(env);
  const storage = dataDirectory(
    dir,
    path.join(__dirname, "..", "flood", "data")
  );
  await storage.prepare();
  // Generate a pool of employees.
  const employerPool: EmployerPool = await EmployerPool.load(
    config("LST_EMPLOYERS_FILE")
  );
  const employeePool: EmployeePool = await EmployeePool.load(
    config("LST_EMPLOYEES_FILE")
  );
  const pools = data.reduce((pools, cfg) => {
    const recordsOfScenario = numRecords * (cfg.chance / 100);
    switch (cfg.scenario) {
      case "PortalClaimSubmit":
      case "FineosClaimSubmit":
        const isPortal = cfg.scenario === "PortalClaimSubmit";
        const claimType = "BHAP";
        const eligible = `LST${
          !isPortal ? "F" : ""
        }${claimType}1` as keyof typeof scenarios;
        const ineligible = eligible.replace("1", "4") as keyof typeof scenarios;
        const recordsOfEligible =
          recordsOfScenario * ((cfg.eligible || 100) / 100);
        // Add eligible employees to the pool
        pools.push(
          ClaimPool.generate(
            employeePool,
            scenarios[eligible].employee,
            scenarios[eligible].claim,
            recordsOfEligible
          )
        );
        if (cfg.eligible !== 100) {
          // Add ineligible employees to the pool
          pools.push(
            ClaimPool.generate(
              employeePool,
              scenarios[ineligible].employee,
              scenarios[ineligible].claim,
              recordsOfScenario * ((100 - (cfg.eligible || 0)) / 100)
            )
          );
        }
        break;
      case "LeaveAdminSelfRegistration":
        pools.push(generateLASRS(employerPool, recordsOfScenario));
        break;
      case "SavilinxAgent":
        pools.push(generateAgents(recordsOfScenario));
        break;
      default:
        throw new Error(`Unknown scenario requested: ${cfg.scenario}`);
    }
    return pools;
  }, [] as AnyIterable<GeneratedClaim | DummyScenarioObject>[]);

  // Dehydrate all the claim pools, which involves saving the claim documents to disk.
  const dehydratedPools = pools.map((pool) =>
    pool instanceof ClaimPool ? pool.dehydrate(storage.documents) : pool
  );

  // Save all data bits to a single JSON file.
  await pipelineP(
    Readable.from(merge(...dehydratedPools)),
    JSONStream.stringify(),
    fs.createWriteStream(storage.claims.replace(".ndjson", ".json"))
  );

  return true;
}

export default generateLSTData;
