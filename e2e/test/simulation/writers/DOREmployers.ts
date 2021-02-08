import stream from "stream";
import { describe, expect, it } from "@jest/globals";
import transformDOREmployers from "../../../src/simulation/writers/DOREmployers";

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
};

export const employers = new Map([[employer.fein, employer]]);

const claim = {
  id: "ABC",
  scenario: "TEST",
  claim: {
    employment_status: null,
    first_name: "Dave",
    last_name: "Smith",
    tax_identifier: "000-00-0000",
    employer_fein: employer.fein,
    date_of_birth: "2020-01-01",
    mass_id: "12345",
  },
  documents: [],
  wages: 4000,
};
export const claims = [claim];

/**
 * This helper allows us to pull out the return value of a transform stream for a given input.
 */
export async function extract(
  inputs: unknown[],
  transform: stream.Duplex
): Promise<string> {
  const chunks: Buffer[] = [];
  return new Promise((resolve, reject) => {
    transform.on("data", (chunk) => {
      chunks.push(Buffer.from(chunk));
    });
    transform.on("error", reject);
    transform.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    inputs.forEach((inputChunk) => transform.write(inputChunk));
    transform.end();
  });
}

describe("DOR Employer File Generator", function () {
  it("should generate a valid employer line", async function () {
    const contents = await extract(claims, transformDOREmployers(employers));
    expect(contents).toMatchInlineSnapshot(`
      "00001John Hancock                                                                                                                                                                                                                                                   1212315       123 Some Way                                                                                                                                                                                                                                                   Boston                        MA01010USA                                                                                                                                                                                                                                                               FF999912319999123120200820000000
      "
    `);
  });
});
