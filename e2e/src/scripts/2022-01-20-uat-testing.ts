import dataDirectory from "../generation/DataDirectory";
import path from "path";
import EmployeePool from "../generation/Employee";
import EmployerPool from "../generation/Employer";
import EmployerIndex from "../generation/writers/EmployerIndex";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";

/**
 * @summary
 *
 * This is a data generation script, roughly consisting of three parts:
 *   1. Employer generation
 *   2. Employee generation
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
 */
(async () => {
  const storage = dataDirectory("2022-01-20-uat-testing");
  await storage.prepare();
  let employerPool: EmployerPool;
  let employeePool: EmployeePool;

  // Part 1: Employer generation.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    // 1.a generate employers
    // 1.b write to employers.json
    (employerPool = EmployerPool.generate(10)),
      await employerPool.save(storage.employers);
    // 2. write withholding data to employers.csv
    await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");
    // 3. generate DOR file for upload to PFML
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

    // 1. generate employers
    employeePool = EmployeePool.merge(
      EmployeePool.generate(200, employerPool, {
        wages: "eligible",
      }),
    );
    // 2. write to employers.json
    await employeePool.save(storage.employees);
    // 3. write to DOR file for upload to PFML
    await DOR.writeEmployeesFile(
      employerPool,
      employeePool,
      storage.dorFile("DORDFML")
    );
    // 4. write employee data to employees.csv
    await EmployeeIndex.write(
      employeePool,
      path.join(storage.dir, "employees.csv")
    );
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
