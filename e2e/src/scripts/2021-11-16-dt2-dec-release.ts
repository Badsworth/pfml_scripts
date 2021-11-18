import dataDirectory from "../generation/DataDirectory";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import EmployerIndex from "../generation/writers/EmployerIndex";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";
import * as scenarios from "../scenarios/2021-11-16-dt2";


(async () => {
  // @todo Rename the data directory as needed.
  const storage = dataDirectory("2021-11-16-dt2-dec-release");
  // <!-- @default
  await storage.prepare();
  let employerPool: EmployerPool;
  let employeePool: EmployeePool;
  let claimPool: ClaimPool;
  // @default -->

  // Part 1: Employer generation.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    throw Error('Test'),
    // @todo Choose number of employers to generate.
    (employerPool = EmployerPool.generate(5)),
      await employerPool.save(storage.employers);
    // <!-- @default
    await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
    // @default -->
  }

  // Part 2: Employee generation.
  try {
    employeePool = await EmployeePool.load(storage.employees);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    throw Error('Test'),
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    employeePool = EmployeePool.merge(
      // @todo Choose number of employees to generate.
      // EmployeePool.generate(90, employerPool, {
      //   // @todo Define employee parameters.
      //   // Usually just the `wages` property.
      //   wages: "eligible",
      //   // @todo OPTIONAL: Add `metadata` property for ad hoc needs.
      //   metadata: { hair: "grey" },
      // }),
      // @todo OPTIONAL: Add more employees with different properties.
      // @example Wages set to "ineligible" vs "eligible".
      EmployeePool.generate(50, employerPool, { wages: "eligible" }),
      EmployeePool.generate(20, employerPool, { wages: 90000 }),
    );
    // <!-- @default
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
    // @default -->
  }

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
    claimPool = ClaimPool.merge(
      ClaimPool.generate(employeePool, scenarios.FSTRUE1.employee, scenarios.FSTRUE1.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE2.employee, scenarios.FSTRUE2.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE3.employee, scenarios.FSTRUE3.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE4.employee, scenarios.FSTRUE4.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE5.employee, scenarios.FSTRUE5.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE6.employee, scenarios.FSTRUE6.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE7.employee, scenarios.FSTRUE7.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE8.employee, scenarios.FSTRUE8.claim, 3),
      ClaimPool.generate(employeePool, scenarios.FSTRUE9.employee, scenarios.FSTRUE9.claim, 6),
      ClaimPool.generate(employeePool, scenarios.FSTRUE10.employee, scenarios.FSTRUE10.claim, 6)
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
