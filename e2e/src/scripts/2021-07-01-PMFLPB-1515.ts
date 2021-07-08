import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import * as scenarios from "../scenarios/cypress";
import config from "../config";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("2021-07-01-PFMLPB-1515");
  await storage.prepare();

  // The "tracker" will prevent us from double-submitting claims, as it prevents submission
  // of claims that have previously been submitted.
  let claimPool: ClaimPool;

  const employeePool = await EmployeePool.load(config("EMPLOYEES_FILE"));

  // Generate a pool of employees.
  try {
    await ClaimPool.load(storage.claims, storage.documents);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    claimPool = ClaimPool.merge(
      ClaimPool.generate(
        employeePool,
        scenarios.MHAP1.employee,
        scenarios.MHAP1.claim,
        100
      )
    );

    await claimPool.save(storage.claims, storage.documents);
    //saves used employees
    // await employeePool.save(storage.employees, storage.usedEmployees);
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
