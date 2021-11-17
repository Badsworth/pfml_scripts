import dataDirectory from "../generation/DataDirectory";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import EmployerIndex from "../generation/writers/EmployerIndex";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";
import * as scenarios from "../scenarios";


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
      EmployeePool.generate(36, employerPool, { wages: "eligible" }),
      EmployeePool.generate(14, employerPool, { wages: 90000 }),
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
    claimPool = ClaimPool.generate(
      employeePool,
      // @todo Set to the EmployeePickSpec of a given ScenarioSpecification.
      scenarios.BHAP1.employee,
      // @todo Set to the ClaimSpecification of a given ScenarioSpecification.
      // @todo To trigger `postSubmit` actions within FINEOS, the ClaimSpecification
      //   must include `{ metadata: { postSubmit: POST_SUBMIT_ACTION }`
      //   where POST_SUBMIT_ACTION = "APPROVE" | "DENY" | "APPROVEDOCS"
      scenarios.BHAP1.claim,
      1
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
