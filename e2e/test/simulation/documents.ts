import fs from "fs";
import os from "os";
import path from "path";
import { beforeAll, afterAll, describe, it, expect } from "@jest/globals";
import {
  generateHCP,
  generateIDBack,
  generateIDFront,
} from "../../src/simulation/documents";
import { ApplicationRequestBody } from "../../src/api";

describe("Documents", function () {
  let tempDir: string;

  beforeAll(async () => {
    tempDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "documents"));
  });

  afterAll(async () => {
    await fs.promises.rmdir(tempDir);
  });

  const claim: ApplicationRequestBody = {
    first_name: "John",
    last_name: "Smith",
    date_of_birth: "2020-06-07",
    employee_ssn: "000-00-0000",
    leave_details: {
      continuous_leave_periods: [
        {
          start_date: "2020-08-01",
          end_date: "2020-09-01",
        },
      ],
    },
  };

  it("Should generate an HCP form", async function () {
    const file = path.join(tempDir, "hcp.pdf");
    await generateHCP(claim, path.join(tempDir, "hcp.pdf"));
    await expect(fs.promises.stat(file)).resolves.toBeTruthy();
  });

  it("Should generate an ID front", async function () {
    const file = path.join(tempDir, "id-front.pdf");
    await generateIDFront(claim, path.join(tempDir, "id-front.pdf"));
    await expect(fs.promises.stat(file)).resolves.toBeTruthy();
  });

  it("Should generate an ID back", async function () {
    const file = path.join(tempDir, "id-back.pdf");
    await generateIDBack(claim, path.join(tempDir, "id-back.pdf"));
    await expect(fs.promises.stat(file)).resolves.toBeTruthy();
  });
});
