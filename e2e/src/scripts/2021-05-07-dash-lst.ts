import dataDirectory from "../generation/DataDirectory";
import path from "path";
import EmployeePool from "../generation/Employee";
import EmployerPool from "../generation/Employer";
import EmployerIndex from "../generation/writers/EmployerIndex";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("2021-06-28-PFMLPB-1517-SET-2");
  await storage.prepare();

  // The "tracker" will prevent us from double-submitting claims, as it prevents submission
  // of claims that have previously been submitted.
  let employerPool: EmployerPool;
  let employeePool: EmployeePool;

  /// Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    (employerPool = EmployerPool.merge(
      EmployerPool.generate(5, { size: "small" })
    )),
      await employerPool.save(storage.employers);
    await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  }

  // Generate a pool of employees.
  try {
    employeePool = await EmployeePool.load(storage.employees);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    employeePool = EmployeePool.merge(
      EmployeePool.generate(200, employerPool, { wages: "eligible" })
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

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
