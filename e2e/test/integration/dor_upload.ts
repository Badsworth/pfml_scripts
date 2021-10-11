import { Environment } from "./../../src/types";
import dataDirectory from "../../src/generation/DataDirectory";
import EmployerPool from "../../src/generation/Employer";
import EmployeePool from "../../src/generation/Employee";
import { format, subDays } from "date-fns";
import InfraClient from "../../src/InfraClient";
import config from "../../src/config";
import fs from "fs";
import path from "path";
import os from "os";
import DOR from "../../src/generation/writers/DOR";
import { Fineos, ClaimantPage } from "../../src/submission/fineos.pages";
import { jest, describe, beforeAll, afterAll, test } from "@jest/globals";

const envs: Environment[] = [
  "test",
  "stage",
  "training",
  "performance",
  "uat",
  "cps-preview",
];
// wait for 20 minutes to complete dor processing
jest.setTimeout(1000 * 60 * 20);

/**
 * @group nightly
 */
describe("dor_upload", () => {
  let tempDir: string;
  const employeeSsnAsDate = (date?: Date) => {
    const formatted = "0" + format(date ?? new Date(), "MM-dd-yyyy");
    return formatted;
  };
  const employerFeinAsDate = (date?: Date) => {
    const dateChars = [
      "0",
      ...format(date ?? new Date(), "MM/dd/yyyy").replace(/\//g, ""),
    ];
    dateChars.splice(2, 0, "-");
    const formatted = dateChars.join("");
    return formatted;
  };

  beforeAll(async () => {
    tempDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "documents"));
  });
  afterAll(async () => {
    if (tempDir) {
      await fs.promises.rmdir(tempDir);
    }
  });

  test(
    "Finds the employee from the previous day",
    async () => {
      const dayOfWeek = format(new Date(), "EEEE");
      const isMonday = dayOfWeek === "Monday";
      await Fineos.withBrowser(
        async (page) => {
          await new ClaimantPage(page).visit(
            employeeSsnAsDate(subDays(new Date(), isMonday ? 3 : 1))
          );
        },
        { debug: false }
      );
    },
    1000 * 60
  );

  test("Uploads and processes DOR files", async () => {
    const env = config("ENVIRONMENT");
    if (!envs.includes(env as Environment))
      throw Error(`Invalid environment: ${env}`);

    const storage = dataDirectory(`dor_upload_test`, tempDir);
    await storage.prepare();
    const infra = new InfraClient(config("ENVIRONMENT"));

    const employerPool = EmployerPool.generate(1, {});
    employerPool.pick().fein = employerFeinAsDate();
    await employerPool.save(storage.employers);

    const employeePool = EmployeePool.generate(1, employerPool, {});
    employeePool.pick({}).ssn = employeeSsnAsDate();
    await employeePool.save(storage.employees);

    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
    await DOR.writeEmployeesFile(
      employerPool,
      employeePool,
      storage.dorFile("DORDFML")
    );

    try {
      await infra.uploadDORFiles([
        storage.dorFile("DORDFMLEMP"),
        storage.dorFile("DORDFML"),
      ]);
      await infra.runDorEtl("success");
    } catch (e) {
      console.error(e);
      throw e;
    }
  });
});
