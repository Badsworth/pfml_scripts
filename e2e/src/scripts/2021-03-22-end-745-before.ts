import * as scenarios from "../scenarios/uat";
import ClaimPool from "../generation/Claim";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import { ScenarioSpecification } from "../generation/Scenario";

import { dataDirectory } from "./util";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("2021-03-22-end-745-before");
  await storage.prepare();

  if (true) {
    // The "tracker" will prevent us from double-submitting claims, as it prevents submission
    // of claims that have previously been submitted.
    let employerPool: EmployerPool;
    let employeePool: EmployeePool;
    let claimPool: ClaimPool;

    /// Generate a pool of employers.
    try {
      employerPool = await EmployerPool.load(storage.employers);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      return;
    }

    // Generate a pool of employees.
    try {
      employeePool = await EmployeePool.load(storage.employees);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      return;
    }

    // Generate a pool of claims. This could happen later, though!
    try {
      claimPool = await ClaimPool.load(storage.claims, storage.documents);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      // // Shortcut for generating a new claim pool filled with 1 scenario.
      const generate = (spec: ScenarioSpecification, count: number) =>
        ClaimPool.generate(
          employeePool,
          spec.employee,
          spec.claim,
          count * 1.1
        );

      await ClaimPool.merge(
        generate(scenarios.UATA, 10),
        generate(scenarios.UATB, 10),
        generate(scenarios.UATC, 10),
        generate(scenarios.UATD, 10),
        generate(scenarios.UATE, 10),
        generate(scenarios.UATF, 10),
        generate(scenarios.UATG, 10),
        generate(scenarios.UATH, 10),
        generate(scenarios.UATI, 10),
        generate(scenarios.UATJ, 10),
        generate(scenarios.UATK, 10),
        generate(scenarios.UATL, 10),
        generate(scenarios.UATM, 5),
        generate(scenarios.UATN, 5),
        generate(scenarios.UATO, 10),
        generate(scenarios.UATP, 5),
        generate(scenarios.UATQ, 5)
      ).save(storage.claims, storage.documents);
    }
  }

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
