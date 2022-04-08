import { Environment } from "./../../src/types";
import dataDirectory from "../../src/generation/DataDirectory";
import EmployerPool from "../../src/generation/Employer";
import EmployeePool from "../../src/generation/Employee";
import {
  endOfQuarter,
  format,
  formatISO,
  subDays,
  subQuarters,
} from "date-fns";
import InfraClient from "../../src/InfraClient";
import config from "../../src/config";
import fs from "fs";
import path from "path";
import os from "os";
import DOR from "../../src/generation/writers/DOR";
import { Fineos, ClaimantPage } from "../../src/submission/fineos.pages";
import { jest, describe, beforeAll, afterAll, test } from "@jest/globals";
import { generateCredentials } from "../../src/util/credentials";
import { getAuthManager } from "../../src/util/common";

const envs: Environment[] = [
  "test",
  "stage",
  "training",
  "performance",
  "uat",
  "cps-preview",
  "breakfix",
  "long",
  "trn2",
];
// wait for 20 minutes to complete dor processing
jest.setTimeout(1000 * 60 * 20);

/**
 * @group morning
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
      await fs.promises.rmdir(tempDir, { recursive: true });
    }
  });

  test(
    "Finds the employee from the previous day",
    async () => {
      const dayOfWeek = format(new Date(), "EEEE");
      const isMonday = dayOfWeek === "Monday";
      // Training refresh takes place Monday morning after testing (before employee's are picked up before the nightly eligibility batch job).
      // This will cause test data from the previous day to be "wiped"
      if (dayOfWeek === "Tuesday" && config("ENVIRONMENT") === "training")
        return;
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
    const infra = InfraClient.create(config);

    const employerPool = EmployerPool.generate(1, {
      fein: employerFeinAsDate(),
    });
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

  test("Register and verify leave admin", async () => {
    const authenticator = getAuthManager();

    const storage = dataDirectory(`dor_upload_test`, tempDir);
    await storage.prepare();
    const employerPool = await EmployerPool.load(storage.employers);

    const employer = employerPool.pick();

    const fein = employer.fein;
    const withholding_amount =
      employer.withholdings[employer.withholdings.length - 1];
    const quarter = formatISO(endOfQuarter(subQuarters(new Date(), 1)), {
      representation: "date",
    });

    const { username, password } = generateCredentials();

    try {
      await authenticator.registerLeaveAdmin(username, password, fein);
    } catch (err) {
      // since we're generating random creds each run, it'd be pretty
      // surprising if we got a repeat email error. regardless, we don't
      // want to fail the whole test if it does happen
      if (err.code !== "UsernameExistsException") {
        throw err;
      }
    }

    await authenticator.verifyLeaveAdmin(
      username,
      password,
      withholding_amount,
      quarter
    );
  }, 90000);
});
