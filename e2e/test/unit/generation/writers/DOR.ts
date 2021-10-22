import { afterAll, beforeAll, describe, expect, it } from "@jest/globals";
import DORWriter from "../../../../src/generation/writers/DOR";
import EmployerPool from "../../../../src/generation/Employer";
import fs from "fs";
import EmployeePool from "../../../../src/generation/Employee";
import path from "path";
import os from "os";

const employer = {
  accountKey: "00001",
  name: "John Hancock",
  fein: "12-12315",
  street: "123 Some Way",
  city: "Boston",
  state: "MA",
  zip: "01010",
  dba: "",
  family_exemption: false,
  medical_exemption: false,
  updated_date: new Date("2020-08-20 00:00:00"),
  withholdings: [0, 0, 0, 0],
};
const employee = {
  first_name: "John",
  last_name: "Smith",
  ssn: "000-00-0000",
  date_of_birth: "2020-01-01",
  occupations: [{ fein: "12-12315", wages: 200 }],
};

const employerPool = new EmployerPool([employer]);
const employeePool = new EmployeePool([employee]);

describe("DOR File Writer", () => {
  let tempdir: string;

  beforeAll(async () => {
    tempdir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "dor"));
  });
  afterAll(async () => {
    if (tempdir) {
      await fs.promises.rmdir(tempdir, { recursive: true });
    }
  });

  it("Should generate valid employer lines", async function () {
    const filename = `${tempdir}/employer.txt`;
    await DORWriter.writeEmployersFile(employerPool, filename);
    await expect(fs.promises.readFile(filename, "utf-8")).resolves
      .toMatchInlineSnapshot(`
            "00001John Hancock                                                                                                                                                                                                                                                   1212315       123 Some Way                                                                                                                                                                                                                                                   Boston                        MA01010USA                                                                                                                                                                                                                                                               FF999912319999123120200820000000
            "
          `);
  });
  it("Should generate valid employer lines", async function () {
    const filename = `${tempdir}/employee.txt`;
    await DORWriter.writeEmployeesFile(
      employerPool,
      employeePool,
      filename,
      new Date(2021, 7, 1)
    );
    await expect(fs.promises.readFile(filename, "utf-8")).resolves
      .toMatchInlineSnapshot(`
            "A0000120200930John Hancock                                                                                                                                                                                                                                                   1212315       F1212315                       0.002020093020200930235959
            A0000120201231John Hancock                                                                                                                                                                                                                                                   1212315       F1212315                       0.002020123120201231235959
            A0000120210331John Hancock                                                                                                                                                                                                                                                   1212315       F1212315                       0.002021033120210331235959
            A0000120210630John Hancock                                                                                                                                                                                                                                                   1212315       F1212315                       0.002021063020210630235959
            B0000120200930John                                                                                                                                                                                                                                                           Smith                                                                                                                                                                                                                                                          000000000FT               50.00               50.00                0.00                0.00                0.00                0.00
            B0000120201231John                                                                                                                                                                                                                                                           Smith                                                                                                                                                                                                                                                          000000000FT              100.00               50.00                0.00                0.00                0.00                0.00
            B0000120210331John                                                                                                                                                                                                                                                           Smith                                                                                                                                                                                                                                                          000000000FT              150.00               50.00                0.00                0.00                0.00                0.00
            B0000120210630John                                                                                                                                                                                                                                                           Smith                                                                                                                                                                                                                                                          000000000FT              200.00               50.00                0.00                0.00                0.00                0.00
            "
          `);
  });
});
