import dataDirectory from "../generation/DataDirectory";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import EmployerIndex from "../generation/writers/EmployerIndex";
import { format } from "date-fns";
import { transform } from "streaming-iterables";
import InfraClient from "../InfraClient";
import { Environment } from "../types";
import AuthManger from "../submission/AuthenticationManager";
import configs from "../../config.json";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import TestMailVerificationFetcher from "../submission/TestMailVerificationFetcher";
import { getLeaveAdminCredentials } from "../util/credentials";
import dotenv from "dotenv";
import { endOfQuarter, formatISO, subQuarters } from "date-fns";
import chalk from "chalk";
dotenv.config();

(async () => {
  const date = format(new Date(), "yyyy-MM-dd");
  const rawConfig = { ...configs };

  // Prepare a "data directory" to save the generated data to disk.
  const storage = dataDirectory(`e2e-${date}`);
  await storage.prepare();

  // Generate 2 employers that will have employees assigned to them.
  const employersWithEmployees = EmployerPool.generate(2, {
    size: "small",
    metadata: { has_employees: true },
  });
  // Generate 1 employer with 0 withholdings for use in LA verification.
  const ineligibleLAEmployers = EmployerPool.generate(1, {
    size: "small",
    withholdings: [0, 0, 0, 0],
    metadata: { register_leave_admins: true },
  });
  // Generate 2 employers with withholdings for use in LA verification.
  const eligibleLAEmployers = EmployerPool.generate(2, {
    size: "small",
    metadata: { register_leave_admins: true },
  });

  // Combine all of our employers into one big pool that we'll save.
  const employerPool = EmployerPool.merge(
    employersWithEmployees,
    ineligibleLAEmployers,
    eligibleLAEmployers
  );
  // Save the employer pool to JSON (employers.json)
  await employerPool.save(storage.employers);
  // Write an employer DOR file.
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  // Write an employer "index" file for human consumption.
  await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");

  // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
  // then we merge them all together.
  const employeePool = EmployeePool.merge(
    EmployeePool.generate(2500, employersWithEmployees, {
      wages: "ineligible",
    }),
    EmployeePool.generate(2500, employersWithEmployees, { wages: 30000 }),
    EmployeePool.generate(2500, employersWithEmployees, { wages: 60000 }),
    EmployeePool.generate(2500, employersWithEmployees, { wages: 90000 })
  );
  // Write the employee pool to disk (employees.json).
  await employeePool.save(storage.employees);
  // Write an employees DOR file to disk.
  await DOR.writeEmployeesFile(
    employerPool,
    employeePool,
    storage.dorFile("DORDFML")
  );
  // Write an employee "index" file for human consumption.
  await EmployeeIndex.write(employeePool, storage.dir + "/employees.csv");

  // Additionally save the JSON files to the employers/employees directory at the top level.
  await employeePool.save(`employees/e2e-${date}.json`);
  await employerPool.save(`employers/e2e-${date}.json`);

  const envs: Environment[] = [
    "test",
    "stage",
    "training",
    "performance",
    "uat",
    "cps-preview",
  ];

  const DORUploadRequest = transform(envs.length, async (env: Environment) => {
    const infra = new InfraClient(env);
    try {
      await infra.uploadDORFiles([
        storage.dorFile("DORDFMLEMP"),
        storage.dorFile("DORDFML"),
      ]);
      await infra.runDorEtl();
    } catch (e) {
      console.log(`${env.toUpperCase()} - failed to load EE's/ER's`);
      console.error(e);
    }
    const authManager = new AuthManger(
      new CognitoUserPool({
        UserPoolId: rawConfig[env].COGNITO_POOL,
        ClientId: rawConfig[env].COGNITO_CLIENTID,
      }),
      rawConfig[env].API_BASEURL,
      new TestMailVerificationFetcher(
        process.env.E2E_TESTMAIL_APIKEY as string,
        rawConfig[env].TESTMAIL_NAMESPACE
      )
    );

    const leaveAdminVerifications = transform(3, async (employer: Employer) => {
      try {
        if (employer.withholdings.some((val) => val === 0)) return;
        const quarter = formatISO(endOfQuarter(subQuarters(new Date(), 1)), {
          representation: "date",
        });
        const { username, password } = getLeaveAdminCredentials(employer.fein);
        await authManager.registerLeaveAdmin(username, password, employer.fein);
        console.log(
          `${chalk.blue(env.toUpperCase())} -  ${username} registered`
        );
        await authManager.verifyLeaveAdmin(
          username,
          password,
          employer.withholdings.pop() as number,
          quarter
        );
        console.log(`${chalk.blue(env.toUpperCase())} -  ${username} verified`);
      } catch (e) {
        console.error(
          `${env.toUpperCase()} - Failed to register and verify employer ${
            employer.fein
          }\n${e.message}`
        );
      }
    });
    for await (const _ of leaveAdminVerifications([...employerPool])) continue;
  });

  for await (const _ of DORUploadRequest(envs)) continue;
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
