import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import * as scenarios from "../scenarios/2021-09-08-training";
import describe from "../specification/describe";
import { promisify } from "util";
import { pipeline } from "stream";
import * as fs from "fs";
import { ScenarioSpecification } from "../generation/Scenario";
import EmployerPool from "../generation/Employer";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import EmployerIndex from "../generation/writers/EmployerIndex";
import path from "path";

const pipelineP = promisify(pipeline);

(async () => {
  const storage = dataDirectory("2021-09-08-training");
  await storage.prepare();

  const employerPool = await EmployerPool.load(
    storage.employers
  ).orGenerateAndSave(() => EmployerPool.generate(5, { size: "small" }));
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(
    employerPool,
    path.join(storage.dir, "employees.csv")
  );

  const employeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      EmployeePool.generate(16000, employerPool, {
        mass_id: true,
        wages: "eligible",
      }),
      EmployeePool.generate(400, employerPool, { wages: "ineligible" })
    )
  );
  await DOR.writeEmployeesFile(
    employerPool,
    employeePool,
    storage.dorFile("DORDFML")
  );
  await EmployeeIndex.write(
    employeePool,
    path.join(storage.dir, "employers.csv")
  );

  const generateClaims = (spec: ScenarioSpecification, count: number) =>
    ClaimPool.generate(employeePool, spec.employee, spec.claim, count);
  await ClaimPool.load(storage.claims, storage.documents).orGenerateAndSave(
    () =>
      ClaimPool.merge(
        ...Object.values(scenarios).map((spec) => {
          if (typeof spec?.claim.metadata?.quantity !== "number")
            throw new Error("Missing 'quantity' value for scenario");
          return generateClaims(spec, spec.claim.metadata.quantity * 1.2);
        })
      )
  );
  // Write a CSV description of the scenarios we're using for human consumption.
  await pipelineP(
    describe(Object.values(scenarios)),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
  );

  // used to generate fresh employees and employers for training
  const claimantsOnlyStorage = dataDirectory(
    "2021-09-08-training-claimants-only"
  );
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
  await EmployerIndex.write(
    claimantsOnlyEmployerPool,
    path.join(claimantsOnlyStorage.dir, "employees.csv")
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
  await EmployeeIndex.write(
    claimantsOnlyEmployeePool,
    path.join(claimantsOnlyStorage.dir, "employers.csv")
  );

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );
  // Catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
