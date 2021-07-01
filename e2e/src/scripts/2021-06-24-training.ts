/**
 * @file
 * Template for generating PFML test data.
 *
 * @abstract
 * Should be cloned in the same directory and customized before use.
 */

import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import {
  TRNER1,
  TRNER2,
  TRNER3,
  TRNOI1,
  TRNOI2,
  TRNOI3,
  TRNOI4,
  TRNOL1,
  TRNOL2,
  TRNOL3,
  TRNOL4,
} from "../scenarios/2021-06-24-training";
import { ScenarioSpecification } from "../generation/Scenario";
import config from "../config";

/**
 * @summary
 *
 * This is a data generation script, roughly consisting of three parts:
 *   1. Employer generation
 *   2. Employee generation
 *   3. Claim generation
 *
 * Clone this file to make a new script. Before use, take note of all @todo items listed below.
 *
 * NB. This script is "idempotent"—if you run it multiple times, nothing bad happens.
 * Since we check if file exists each time, we may rerun this many times without overwriting existing data.
 *
 * @todo After customizing this script, you can generate the data by running:
 *   ```
 *     npx ts-node [PATH/TO/DATA_GEN_SCRIPT.ts]`
 *   ```
 *
 * By default, the resulting data will be placed within the `/data` directory at the project root.
 *
 * @todo After generating the data, follow-up steps may include:
 *   1. Upload the resulting DOR files to the appropriate S3 bucket based on the desired environment;
 *   2. After the employers are loaded into FINEOS, register Leave Admins for the employers by running:
 *     ```
 *       E2E_ENVIRONMENT=ENV_NAME npm run cli -- simulation registerAllLeaveAdmins [-f PATH/TO/employers.json]
 *     ```
 *   2a. To register a single Leave Admin at a time, use the following command instead:
 *     ```
 *       npm run cli -- simulation register-leave-admin [FEIN] [WITHHOLDING_AMOUNT]
 *     ```
 *   3. Submit the generated claims by running:
 *     ```
 *       npx ts-node e2e/src/scripts/submit.ts [PATH/TO/DATA/DIR] [CONCURRENCY]
 *     ```
 *   3a. If the claims have `postSubmit` steps, then Leave Admins must be registered before claim submission.
 */
(async () => {
  // @todo Rename the data directory as needed.
  const storage = dataDirectory("2021-06-25-OLB_training_claims");
  // <!-- @default
  await storage.prepare();
  let claimPool: ClaimPool;
  // @default -->

  const employeePool = await EmployeePool.load(config("EMPLOYEES_FILE"));

  // Part 3: Claim generation.
  try {
    await ClaimPool.load(storage.claims, storage.documents);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    /*
     * @todo Define the kinds of employees we need to support.
     *
     * Each type of employee is generated as its own pool,
     * then we merge them all together.
     *
     * @see ScenarioSpecification for expected structure.
     * @see `e2e/src/scenarios` for examples.
     *
     * NOTE: Scenarios may be defined here ad hoc, rather than being
     * defined within the `e2e/src/scenarios` directory, if they are
     * not meant to be reused elsewhere.
     */

    const generate = (spec: ScenarioSpecification, count: number) =>
      ClaimPool.generate(employeePool, spec.employee, spec.claim, count);
    claimPool = ClaimPool.merge(
      generate(TRNOI1, 1),
      generate(TRNOI2, 1),
      generate(TRNOI3, 1),
      generate(TRNOI4, 1),
      generate(TRNOL1, 1),
      generate(TRNOL2, 1),
      generate(TRNOL3, 1),
      generate(TRNOL4, 1),
      generate(TRNER1, 1),
      generate(TRNER2, 1),
      generate(TRNER3, 1)
    );
    // <!-- @default
    await claimPool.save(storage.claims, storage.documents);
    // Save used employees.
    // @todo OPTIONAL: Omit second arg to reuse employees.
    await employeePool.save(storage.employees, storage.usedEmployees);
    // @default -->
  }
  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );
  // Catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
