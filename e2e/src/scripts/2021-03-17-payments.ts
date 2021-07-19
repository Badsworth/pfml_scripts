import ClaimPool from "../generation/Claim";
import dataDirectory from "../generation/DataDirectory";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import * as scenarios from "../scenarios/payments";
import DOR from "../generation/writers/DOR";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("payments-2021-03-19");
  await storage.prepare();

  let employerPool: EmployerPool;
  let employeePool: EmployeePool;

  // Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    employerPool = EmployerPool.generate(1);
    await employerPool.save(storage.employers);
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  }

  // Generate a pool of employees.
  try {
    employeePool = await EmployeePool.load(storage.employees);
  } catch (e) {
    employeePool = EmployeePool.merge(
      ...Object.entries(scenarios).map(([, scenario]) => {
        return EmployeePool.generate(100, employerPool, scenario.employee);
      })
    );
    employeePool.save(storage.employees);
    await DOR.writeEmployeesFile(
      employerPool,
      employeePool,
      storage.dorFile("DORDFML")
    );
  }

  // Generate a pool of claims. This could happen later, though!
  try {
    await ClaimPool.load(storage.claims, storage.documents);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    await ClaimPool.merge(
      ...Object.entries(scenarios).map(([, spec]) => {
        return ClaimPool.generate(employeePool, spec.employee, spec.claim, 25);
      })
    ).save(storage.claims, storage.documents);
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
