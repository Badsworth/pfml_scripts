import ClaimPool from "../generation/Claim";
import path from "path";
import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import describe from "../specification/describe";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline } from "stream";
import EmployerPool from "../generation/Employer";
import EmployerIndex from "../generation/writers/EmployerIndex";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import * as scenarios from "../scenarios/payments-2021-04-02";

const pipelineP = promisify(pipeline);

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("2021-04-22-perf-payments");
  await storage.prepare();

  // The "tracker" will prevent us from double-submitting claims, as it prevents submission
  // of claims that have previously been submitted.
  let employerPool: EmployerPool;
  let employeePool: EmployeePool;

  /// Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    throw e;
    if (e.code !== "ENOENT") throw e;
    (employerPool = EmployerPool.generate(1)),
      await employerPool.save(storage.employers);
    await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  }

  // Generate a pool of employees.
  try {
    employeePool = await EmployeePool.load(
      storage.dir + "/employees.filtered.4-22.json"
    );
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    throw e;
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    employeePool = EmployeePool.merge(
      ...Object.entries(scenarios).map(([, spec]) => {
        return EmployeePool.generate(35, employerPool, spec.employee);
      })
    );

    await employeePool.save(storage.employees);
    await DOR.writeEmployeesFile(
      employerPool,
      employeePool,
      storage.dorFile("DORDFML")
    );
    await EmployeeIndex.write(
      employeePool,
      path.join(storage.dir, "employees.csv")
    );
  }
  await pipelineP(
    describe(Object.values(scenarios)),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
  );

  // Generate a pool of claims. This could happen later, though!
  const claimPool = ClaimPool.load(
    storage.dir + "/claims_corrected.ndjson",
    storage.documents
  );
  // ).catch(async (e) => {
  //   if (e.code !== "ENOENT") throw e;

  //   const cp = ClaimPool.merge(
  //     ...Object.entries(scenarios).map(([, spec]) => {
  //       const employeeSpec =
  //         typeof spec.employee === "function"
  //           ? { wages: 30000 }
  //           : spec.employee;
  //       return ClaimPool.generate(employeePool, employeeSpec, spec.claim, 8);
  //     })
  //   );
  //   await cp.save(storage.dir + "/claims_corrected.ndjson", storage.documents);
  // });

  if (claimPool) console.log("No new claims created");
  else console.log("New claims created");

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
