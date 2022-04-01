import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import {
  scenariosWithValidEmployerAddress,
  scenariosWithInvalidEmployerAdress,
} from "../scenarios/2022-03-24-PFMLPB-3688-ER-RE";
import describe from "../specification/describe";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline } from "stream";
import EmployerPool from "../generation/Employer";
import DOR from "../generation/writers/DOR";
import EmployerIndex from "../generation/writers/EmployerIndex";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";
import { collect } from "streaming-iterables";

const pipelineP = promisify(pipeline);

(async () => {
  const storage = dataDirectory("2022-03-24-PFMLPB-3688-ER-RE");
  await storage.prepare();
  const claimsPerScenario = 25 * 1.2;
  const totalToBeGenerated =
    (scenariosWithInvalidEmployerAdress.length +
      1 +
      (scenariosWithValidEmployerAddress.length + 1)) *
    claimsPerScenario;

  const validAddressEmployers = await EmployerPool.load(
    storage.join("valid_address_ERs.json")
  ).orGenerateAndSave(() => {
    return EmployerPool.merge(
      EmployerPool.generate(1, {
        address: {
          line_1: "4 Kevin Dr",
          city: "Assonet",
          state: "MA",
          zip: "02702-1108",
        },
        size: "medium",
        metadata: { validAdress: true },
      }),
      EmployerPool.generate(1, {
        address: {
          line_1: "19 Lake St",
          city: "Millbury",
          state: "MA",
          zip: "01527-3315",
        },
        size: "medium",
        metadata: { validAdress: true },
      }),
      EmployerPool.generate(1, {
        address: {
          line_1: "22 Cabot Rd",
          city: "Lawrence",
          state: "MA",
          zip: "01843-3802",
        },
        size: "medium",
        metadata: { validAdress: true },
      }),
      EmployerPool.generate(1, {
        address: {
          line_1: "117 Wilson St",
          city: "Brockton",
          state: "MA",
          zip: "02301-6334",
        },
        size: "medium",
        metadata: { validAdress: true },
      })
    );
  });

  const invalidAddressEmployers = await EmployerPool.load(
    storage.join("invalid_address_ERs.json")
  ).orGenerateAndSave(() => {
    return EmployerPool.generate(4, {
      size: "medium",
      metadata: { validAdress: false },
    });
  });

  const allEmployers = await EmployerPool.merge(
    validAddressEmployers,
    invalidAddressEmployers
  );

  await allEmployers.save(storage.employers);

  await DOR.writeEmployersFile(allEmployers, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(
    allEmployers,
    path.join(storage.dir, "employers.csv")
  );

  const employeesWithValidEmployer = await EmployeePool.load(
    storage.join("employees_with_valid_ERs.json")
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      // RE_PYMT_1
      EmployeePool.generate(300, validAddressEmployers, {
        mass_id: true,
        wages: 90000,
        metadata: { prenoted: "yes" },
      }),
      // RE_PYMT2, RE_PYMT4
      EmployeePool.generate(600, validAddressEmployers, {
        mass_id: true,
        wages: 60000,
        metadata: { prenoted: "yes" },
      }),
      // RE_PYMT3, RE_PYMT_5, RE_PYMT_8, RE_PYMT_10
      EmployeePool.generate(1200, validAddressEmployers, {
        mass_id: true,
        wages: 30000,
        metadata: { prenoted: "yes" },
      })
    )
  );

  const employeesWithInvalidEmployer = await EmployeePool.load(
    storage.join("employees_with_invalid_ERs.json")
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      // RE_PYMT_6
      EmployeePool.generate(300, invalidAddressEmployers, {
        mass_id: true,
        wages: 90000,
        metadata: { prenoted: "yes" },
      }),
      // RE_PYMT_7, RE_PYMT_9
      EmployeePool.generate(600, invalidAddressEmployers, {
        mass_id: true,
        wages: 60000,
        metadata: { prenoted: "yes" },
      })
    )
  );

  const employeePool = EmployeePool.merge(
    employeesWithInvalidEmployer,
    employeesWithValidEmployer
  );
  await employeePool.save(storage.employees);

  await DOR.writeEmployeesFile(
    allEmployers,
    employeePool,
    storage.dorFile("DORDFML")
  );
  await EmployeeIndex.write(
    employeePool,
    path.join(storage.dir, "employees.csv")
  );

  const totalEmployees = await collect(employeePool).length;
  const possibleClaimPools = Math.floor(totalEmployees / totalToBeGenerated);
  const iterations = possibleClaimPools;
  for (let i = 1; i <= iterations; i++) {
    const claimFileName = path.join(
      path.dirname(storage.claims),
      `${path.basename(storage.claims, ".ndjson")}_${i}${path.extname(
        storage.claims
      )}`
    );
    console.log(`Generating and Saving to ${claimFileName}`);
    await ClaimPool.load(claimFileName, storage.documents).orGenerateAndSave(
      () =>
        ClaimPool.merge(
          ...Object.values(scenariosWithValidEmployerAddress).map(
            (scenario) => {
              return ClaimPool.generate(
                employeesWithValidEmployer,
                scenario.employee,
                scenario.claim,
                claimsPerScenario
              );
            }
          ),
          ...Object.values(scenariosWithInvalidEmployerAdress).map(
            (scenario) => {
              return ClaimPool.generate(
                employeesWithInvalidEmployer,
                scenario.employee,
                scenario.claim,
                claimsPerScenario
              );
            }
          )
        )
    );
  }

  // Write a CSV description of the scenarios we're using for human consumption.
  await pipelineP(
    describe(
      Object.values([
        ...scenariosWithValidEmployerAddress,
        ...scenariosWithInvalidEmployerAdress,
      ])
    ),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
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
