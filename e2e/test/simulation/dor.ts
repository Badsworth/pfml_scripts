import {
  createEmployeesStream,
  createEmployersStream,
} from "../../src/simulation/dor";
import { describe, it, expect } from "@jest/globals";

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
  updated_date: new Date("2020-08-20"),
};

/**
 * Utility to extract a readable stream to a string.
 *
 * @param stream
 */
function extract(stream: NodeJS.ReadableStream) {
  const chunks: Buffer[] = [];
  return new Promise((resolve, reject) => {
    stream.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
    stream.on("error", reject);
    stream.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
  });
}

describe("DOR Employer File Generator", function () {
  it("should generate a valid employer line", async function () {
    const contents = await extract(createEmployersStream([employer, employer]));
    expect(contents).toMatchInlineSnapshot(`
      "00001John Hancock                                                                                                                                                                                                                                                   1212315123 Some Way                                                                                                                                                                                                                                                   Boston                        MA01010                                                                                                                                                                                                                                                               FF999912319999123120200820000000
      00001John Hancock                                                                                                                                                                                                                                                   1212315123 Some Way                                                                                                                                                                                                                                                   Boston                        MA01010                                                                                                                                                                                                                                                               FF999912319999123120200820000000
      "
    `);
  });
});

const filingPeriods = [new Date("2020-06-30")];

describe("DOR Employee File Generator", function () {
  it("should generate a valid employee line", async function () {
    const claim = {
      scenario: "TEST",
      claim: {
        employment_status: null,
        first_name: "Dave",
        last_name: "Smith",
        employee_ssn: "000-00-0000",
        employer_fein: employer.fein,
        date_of_birth: "2020-01-01",
        mass_id: "12345",
      },
      documents: [],
    };
    const contents = await extract(
      createEmployeesStream([claim], [employer, employer], filingPeriods)
    );

    expect(contents).toMatchInlineSnapshot(`
      "A0000120200630John Hancock                                                                                                                                                                                                                                                   1212315F2020063020200630000000
      A0000120200630John Hancock                                                                                                                                                                                                                                                   1212315F2020063020200630000000
      B0000120200630Dave                                                                                                                                                                                                                                                           Smith                                                                                                                                                                                                                                                          000000000FT             1276.00             1276.00                0.00                0.00                0.00                0.00
      "
    `);
  });
});
