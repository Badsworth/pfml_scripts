import path from "path";
import * as scenarios from "../scenarios";
import ClaimPool from "../generation/Claim";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import { ScenarioSpecification } from "../generation/Scenario";
import DOR from "../generation/writers/DOR";
import dataDirectory from "../generation/DataDirectory";
import EmployerIndex from "../generation/writers/EmployerIndex";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("2021-03-17-TRAINING");
  await storage.prepare();

  if (true) {
    // The "tracker" will prevent us from double-submitting claims, as it prevents submission
    // of claims that have previously been submitted.
    let employerPool: EmployerPool;
    let employeePool: EmployeePool;

    /// Generate a pool of employers.
    try {
      employerPool = await EmployerPool.load(storage.employers);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      (employerPool = EmployerPool.generate(1)),
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
        EmployeePool.generate(9600, employerPool, {
          wages: "eligible",
        }),
        EmployeePool.generate(400, employerPool, {
          wages: "ineligible",
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
    // Generate a pool of claims. This could happen later, though!
    try {
      await ClaimPool.load(storage.claims, storage.documents);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      // Shortcut for generating a new claim pool filled with 1 scenario.
      const generate = (spec: ScenarioSpecification, count: number) =>
        ClaimPool.generate(
          employeePool,
          spec.employee,
          spec.claim,
          count * 1.1
        );

      await ClaimPool.merge(
        generate(scenarios.TRNA, 20),
        generate(scenarios.TRNB, 80),
        generate(scenarios.TRNC, 200),
        generate(scenarios.TRND, 20),
        generate(scenarios.TRNE, 150),
        generate(scenarios.TRNF, 150),
        generate(scenarios.TRNG, 300),
        generate(scenarios.TRNH, 300),
        generate(scenarios.TRNI, 20),
        generate(scenarios.TRNJ, 50),
        generate(scenarios.TRNK, 50),
        generate(scenarios.TRNL, 100),
        generate(scenarios.TRNM, 200),
        generate(scenarios.TRNN, 100),
        generate(scenarios.TRNO, 100),
        generate(scenarios.TRNP, 100),
        generate(scenarios.TRNQ, 20),
        generate(scenarios.TRNR, 80),
        generate(scenarios.TRNS, 20),
        generate(scenarios.TRNT, 20),
        generate(scenarios.TRNU, 150),
        generate(scenarios.TRNV, 150),
        generate(scenarios.TRNW, 150),
        generate(scenarios.TRNX, 150),
        generate(scenarios.TRNY, 300),
        generate(scenarios.TRNZ, 20),
        generate(scenarios.TRNAA, 200),
        generate(scenarios.TRNAB, 200),
        generate(scenarios.TRNAC, 200),
        generate(scenarios.TRNAD, 100),
        generate(scenarios.TRNAE, 100)
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
