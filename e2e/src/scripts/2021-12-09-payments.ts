import ClaimPool from "../generation/Claim";
import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import scenarios, { WITHHOLDING_RETRO } from "../scenarios/payments-2021-12-09";
import describe from "../specification/describe";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline } from "stream";
import EmployerPool from "../generation/Employer";
import DOR from "../generation/writers/DOR";
import EmployerIndex from "../generation/writers/EmployerIndex";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";
import { collect, map, filter } from "streaming-iterables";
const pipelineP = promisify(pipeline);

(async () => {
  const storage = dataDirectory("payments-2021-12-09-payments");
  await storage.prepare();

  const employerPool = await EmployerPool.load(storage.employers);
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(
    employerPool,
    path.join(storage.dir, "employees.csv")
  );

  const employeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      EmployeePool.generate(600, employerPool, {
        mass_id: true,
        wages: 30000,
        metadata: { prenoted: "no" },
      }),
      EmployeePool.generate(300, employerPool, {
        mass_id: true,
        wages: 30000,
        metadata: { prenoted: "yes" },
      }),
      EmployeePool.generate(60, employerPool, {
        mass_id: true,
        wages: 30000,
        metadata: { prenoted: "pending" },
      })
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

  // Write a CSV description of the scenarios we're using for human consumption.
  await pipelineP(
    describe(Object.values([...scenarios, WITHHOLDING_RETRO])),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
  );

  // Attempt to load a claim pool if one has already been generated and saved.
  // If we error out here, we go into generating and saving the pool.

  const claims = await ClaimPool.load(
    storage.claims,
    storage.documents
  ).orGenerateAndSave(() =>
    ClaimPool.merge(
      ...scenarios.map((scenario) =>
        ClaimPool.generate(
          employeePool,
          scenario.employee,
          scenario.claim,
          (scenario.claim.metadata?.quantity as number) * 1.2
        )
      ),
      ClaimPool.generate(
        employeePool,
        WITHHOLDING_RETRO.employee,
        WITHHOLDING_RETRO.claim,
        30 * 1.2
      )
    )
  );

  const usedSSNS = await (
    await collect(claims)
  ).reduce((ssns, claim) => {
    ssns.add(claim.claim.tax_identifier as string);
    return ssns;
  }, new Set<string>());

  const freshEmployees = new EmployeePool(
    await collect(
      await filter((emp) => {
        return !usedSSNS.has(emp.ssn);
      }, employeePool)
    )
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
