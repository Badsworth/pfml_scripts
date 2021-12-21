import ClaimPool from "../generation/Claim";
import dataDirectory from "../generation/DataDirectory";
import EmployeePool, {Employee} from "../generation/Employee";
import scenarios, {WITHHOLDING_RETRO} from "../scenarios/payments-2021-12-09";
import describe from "../specification/describe";
import * as fs from "fs";
import {promisify} from "util";
import {pipeline} from "stream";
import EmployerPool from "../generation/Employer";
import DOR from "../generation/writers/DOR";
import EmployerIndex from "../generation/writers/EmployerIndex";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";
import {collect, map, filter} from "streaming-iterables";

const pipelineP = promisify(pipeline);

(async () => {
  const dataFolderName = "payments-2021-12-18-payments-local"
  console.log(`Starting up. Using data folder ${dataFolderName}`)
  const storage = dataDirectory(dataFolderName);
  await storage.prepare();
  const claimsPerScinario = 8;
  const maxClaimsToGenerate = null;
  const totalToBeGenerated = ((scenarios.length + 1) * claimsPerScinario);
  // SET THIS TRUE IF YOU DON'T HAVE A FOLDER YET
  const FirstPass = true;


  const employerPool = await EmployerPool.load(storage.employers).orGenerateAndSave(
    () => EmployerPool.generate(
      3, {}
    )
  );
  await EmployerIndex.write(
    employerPool,
    path.join(storage.dir, "employers.csv")
  );

  const employeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      EmployeePool.generate(1200, employerPool, {
        mass_id: true,
        wages: 30000,
        metadata: {prenoted: "no"},
      }),
      EmployeePool.generate(600, employerPool, {
        mass_id: true,
        wages: 30000,
        metadata: {prenoted: "yes"},
      }),
      EmployeePool.generate(120, employerPool, {
        mass_id: true,
        wages: 30000,
        metadata: {prenoted: "pending"},
      })
    )
  );

  if (FirstPass) {
    if(!fs.readdirSync(storage.dir).filter(fn => fn.startsWith('DORDFMLEMP_')).length) {
      console.log('Generating Employer DOR file')
      await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
    }
    if(!fs.readdirSync(storage.dir).filter(fn => fn.startsWith('DORDFML_')).length) {
      console.log('Generating Employee DOR file')
      await DOR.writeEmployeesFile(
        employerPool,
        employeePool,
        storage.dorFile("DORDFML")
      );
    }
  }
  await EmployeeIndex.write(
    employeePool,
    path.join(storage.dir, "employee.csv")
  );
  // Write a CSV description of the scenarios we're using for human consumption.
  await pipelineP(
    describe(Object.values([...scenarios, WITHHOLDING_RETRO])),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
  );

  const files = fs
    .readdirSync(storage.dir)
    .filter((fn) => fn.endsWith(".ndjson"));

  const claims = ClaimPool.merge(
    ...(await collect(
      await map(
        async (file) =>
          await ClaimPool.load(path.join(storage.dir, file), storage.documents),
        files
      )
    ))
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


  const totalClaimsPossible = Math.floor(freshEmployees.size() / totalToBeGenerated);
  let iterations = totalClaimsPossible;
  if(maxClaimsToGenerate !== null || (maxClaimsToGenerate !== null && Number(maxClaimsToGenerate) <= totalClaimsPossible)) {
    iterations = Number(maxClaimsToGenerate);
  }

  console.log(`Loaded ${employeePool.size()} Employees, ${usedSSNS.size} are already used,  ${freshEmployees.size()} Available`)
  const i = 1;
  if (iterations > 0) {
    console.log(`Generating ${iterations} Claim files with ${totalToBeGenerated} Claims Each`)
    for (let i = 1; i <= iterations; i++) {
      let claimFileName = path.join(path.dirname(storage.claims),
        `${path.basename(storage.claims, '.ndjson')}_${i}${path.extname(storage.claims)}`,
      )
      console.log(`Generating and Saving to ${claimFileName}`);
      await ClaimPool.load(claimFileName, storage.documents).orGenerateAndSave(
        () =>
          ClaimPool.merge(
            ...scenarios.map((scenario) =>
              ClaimPool.generate(
                freshEmployees,
                scenario.employee,
                scenario.claim,
                claimsPerScinario
              )
            ),
            ClaimPool.generate(
              freshEmployees,
              WITHHOLDING_RETRO.employee,
              WITHHOLDING_RETRO.claim,
              claimsPerScinario
            )
          )
      );
    }
  } else {
    console.log(`Not enough employees to generate all claims needed`)
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
