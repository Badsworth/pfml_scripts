import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import * as scenarios from "../scenarios";
import DOR from "../generation/writers/DOR";
import dataDirectory from "../generation/DataDirectory";
import { ScenarioSpecification } from "../generation/Scenario";
import { format } from "date-fns";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */
(async () => {
  const date = format(new Date(), "yyyy-MM-dd");
  // storage used for claim submission
  const storage = dataDirectory(`${date}-training`);
  await storage.prepare();
  // Generate a pool of employers.
  const employerPool: EmployerPool = await EmployerPool.load(
    storage.employers
  ).orGenerateAndSave(() => EmployerPool.generate(5));
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));

  // Generate a pool of employees.
  const employeePool: EmployeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    EmployeePool.merge(
      EmployeePool.generate(13000, employerPool, { wages: "eligible" }),
      EmployeePool.generate(400, employerPool, { wages: "ineligible" })
    )
  );
  await DOR.writeEmployeesFile(
    employerPool,
    employeePool,
    storage.dorFile("DORDFML")
  );

  // Generate a pool of claims. This could happen later, though!
  await ClaimPool.load(storage.claims, storage.documents).orGenerateAndSave(
    () => {
      // Define the kinds of claims we need to generate.  Each type of claim is defined as its own pool, which we merge
      // together into one big pool.
      const generate = (spec: ScenarioSpecification, count: number) =>
        ClaimPool.generate(employeePool, spec.employee, spec.claim, count);
      return ClaimPool.merge(
        generate(scenarios.TRNA, 20),
        generate(scenarios.TRNB, 80),
        generate(scenarios.TRNC, 200),
        generate(scenarios.TRND, 100),
        generate(scenarios.TRNE, 150),
        generate(scenarios.TRNF, 150),
        generate(scenarios.TRNG, 150),
        generate(scenarios.TRNG2, 150),
        generate(scenarios.TRNH, 300),
        generate(scenarios.TRNI, 100),
        generate(scenarios.TRNJ, 50),
        generate(scenarios.TRNK, 50),
        generate(scenarios.TRNL, 100),
        generate(scenarios.TRNM, 200),
        generate(scenarios.TRNN, 100),
        generate(scenarios.TRNO, 100),
        generate(scenarios.TRNP, 100),
        generate(scenarios.TRNQ, 100),
        generate(scenarios.TRNR, 80),
        generate(scenarios.TRNS, 20),
        generate(scenarios.TRNT, 100),
        generate(scenarios.TRNU, 150),
        generate(scenarios.TRNV, 150),
        generate(scenarios.TRNW, 150),
        generate(scenarios.TRNX, 150),
        generate(scenarios.TRNY, 300),
        generate(scenarios.TRNZ, 100),
        generate(scenarios.TRNAA, 200),
        generate(scenarios.TRNAB, 200),
        generate(scenarios.TRNAC, 200),
        generate(scenarios.TRNAD, 100),
        generate(scenarios.TRNAE, 100),
        generate(scenarios.TRNAF, 200),
        generate(scenarios.TRNAG, 100),
        generate(scenarios.TRNAH, 150),
        generate(scenarios.TRNAI, 150),
        generate(scenarios.TRNAJ, 150),
        generate(scenarios.TRNAK, 150),
        generate(scenarios.TRNAL, 300),
        generate(scenarios.TRNAM, 100),
        generate(scenarios.TRNAN1, 50),
        generate(scenarios.TRNAN2, 50),
        generate(scenarios.TRNAO, 100),
        generate(scenarios.TRNAP, 200),
        generate(scenarios.TRNAQ1, 50),
        generate(scenarios.TRNAQ2, 50),
        generate(scenarios.TRNAR, 100),
        generate(scenarios.TRNAS, 100),
        generate(scenarios.TRNAT, 100)
      );
    }
  );

  // used to generate fresh employees and employers for training
  const claimantsOnlyStorage = dataDirectory(`${date}-training-claimants-only`);
  await claimantsOnlyStorage.prepare();
  // Generate a pool of employers.
  const claimantsOnlyEmployerPool: EmployerPool = await EmployerPool.load(
    claimantsOnlyStorage.employers
  ).orGenerateAndSave(() =>
    EmployerPool.merge(
      EmployerPool.generate(1, { size: "large" }),
      EmployerPool.generate(1, {
        size: "small",
        family_exemption: true,
        medical_exemption: true,
      })
    )
  );

  await DOR.writeEmployersFile(
    claimantsOnlyEmployerPool,
    claimantsOnlyStorage.dorFile("DORDFMLEMP")
  );

  // Generate a pool of employees.
  const claimantsOnlyEmployeePool: EmployeePool = await EmployeePool.load(
    claimantsOnlyStorage.employees
  ).orGenerateAndSave(() =>
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    EmployeePool.generate(1000, claimantsOnlyEmployerPool, {
      wages: "eligible",
    })
  );

  await DOR.writeEmployeesFile(
    claimantsOnlyEmployerPool,
    claimantsOnlyEmployeePool,
    claimantsOnlyStorage.dorFile("DORDFML")
  );

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
