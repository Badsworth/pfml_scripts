import * as JSONStream from "JSONStream";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline, Readable } from "stream";
import { AnyIterable } from "streaming-iterables";
import { DataDirectory } from "../generation/DataDirectory";
import * as scenarios from "../scenarios";
import { ApplicationRequestBody } from "../api";
import config from "../config";
import EmployeePool from "../generation/Employee";
import ClaimPool, { GeneratedClaim } from "../generation/Claim";
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
  storage: DataDirectory,
  numRecords: number,
  scenario: string
): Promise<boolean> {
  // Generate a pool of employees.
  const employerPool: EmployerPool = await EmployerPool.load(
    config("LST_EMPLOYERS_FILE")
  );
  const employeePool: EmployeePool = await EmployeePool.load(
    config("LST_EMPLOYEES_FILE")
  );
  let pool: AnyIterable<GeneratedClaim | DummyScenarioObject>;
  switch (scenario) {
    case "PortalClaimSubmit":
      pool = ClaimPool.merge(
        // 50% of claims will involve other leaves and benefits.
        ClaimPool.generate(
          employeePool,
          scenarios.LSTOLB1.employee,
          scenarios.LSTOLB1.claim,
          Math.floor(numRecords * 0.5)
        ),
        // 30% will be standard bonding claims.
        ClaimPool.generate(
          employeePool,
          scenarios.LSTBHAP1.employee,
          scenarios.LSTBHAP1.claim,
          Math.floor(numRecords * 0.3)
        ),
        // 20% will be standard caring leave claims.
        ClaimPool.generate(
          employeePool,
          scenarios.LSTCHAP1.employee,
          scenarios.LSTCHAP1.claim,
          Math.floor(numRecords * 0.2)
        )
      );
      break;
    case "FineosClaimSubmit":
      pool = ClaimPool.generate(
        employeePool,
        scenarios.LSTFBHAP1.employee,
        scenarios.LSTFBHAP1.claim,
        numRecords
      );
      break;
    case "LeaveAdminSelfRegistration":
      pool = generateLASRS(employerPool, numRecords);
      break;
    case "SavilinxAgent":
      pool = generateAgents(numRecords);
      break;
    default:
      throw new Error(`Unknown LST scenario given: ${scenario}`);
  }
  await pipelineP(
    Readable.from(
      pool instanceof ClaimPool ? pool.dehydrate(storage.documents) : pool
    ),
    JSONStream.stringify(),
    fs.createWriteStream(storage.claims.replace(".ndjson", ".json"))
  );

  return true;
}

export default generateLSTData;
