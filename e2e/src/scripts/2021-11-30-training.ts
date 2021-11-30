import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import * as scenarios from "../scenarios/2021-11-30-training";
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
  const storage = dataDirectory("2021-12-06-training");
  await storage.prepare();

  const employerPool = await EmployerPool.load(
    storage.employers
  ).orGenerateAndSave(() => EmployerPool.generate(2, { size: "small" }));
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(
    employerPool,
    path.join(storage.dir, "employees.csv")
  );

  const employeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    EmployeePool.generate(2000, employerPool, {
      mass_id: true,
      wages: "eligible",
    })
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
        generateClaims(scenarios.TRND, 60),
        generateClaims(scenarios.TRNG, 120),
        generateClaims(scenarios.TRNG_JAN, 120),
        generateClaims(scenarios.TRNH, 120),
        generateClaims(scenarios.TRNT, 60),
        generateClaims(scenarios.TRNW, 120),
        generateClaims(scenarios.TRNW_JAN, 120),
        generateClaims(scenarios.TRNY, 120),
        generateClaims(scenarios.TRNAJ, 120),
        generateClaims(scenarios.TRNAJ_JAN, 120),
        generateClaims(scenarios.TRNAL, 120),
        generateClaims(scenarios.TRNAM, 60)
      )
  );

  // Write a CSV description of the scenarios we're using for human consumption.
  await pipelineP(
    describe(Object.values(scenarios)),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
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
