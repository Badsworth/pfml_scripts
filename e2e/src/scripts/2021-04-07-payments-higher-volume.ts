import ClaimPool from "../generation/Claim";
import EmployeePool from "../generation/Employee";
import dataDirectory from "../generation/DataDirectory";
import * as scenarios from "../scenarios/payments-2021-04-02";
import describe from "../specification/describe";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline } from "stream";

const pipelineP = promisify(pipeline);

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("payments-2021-04-07-payments-higher-volume");
  await storage.prepare();
  const employees = await EmployeePool.load(storage.employees);

  await pipelineP(
    describe(Object.values(scenarios)),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
  );

  // Generate a pool of claims. This could happen later, though!
  await ClaimPool.load(storage.claims, storage.documents).catch(async (e) => {
    if (e.code !== "ENOENT") throw e;

    const cp = ClaimPool.merge(
      ...Object.entries(scenarios).map(([, spec]) => {
        const employeeSpec =
          typeof spec.employee === "function"
            ? { wages: 30000 }
            : spec.employee;
        return ClaimPool.generate(employees, employeeSpec, spec.claim, 8);
      })
    );
    await cp.save(storage.claims, storage.documents);
    return ClaimPool.load(storage.claims, storage.documents);
  });

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
