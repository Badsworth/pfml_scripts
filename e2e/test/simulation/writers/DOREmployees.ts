import { describe, expect, it } from "@jest/globals";
import {
  transformDOREmployeesEmployerLines,
  transformDOREmployeesWageLines,
} from "../../../src/simulation/writers/DOREmployees";
import { claims, employers, extract } from "./DOREmployers";

const filingPeriods = [new Date("2020-06-30")];

describe("DOR Employee File Generator", function () {
  it("should generate a valid employeer line", async function () {
    const contents = await extract(
      claims,
      transformDOREmployeesEmployerLines(employers, filingPeriods)
    );

    expect(contents).toMatchInlineSnapshot(`
      "A0000120200630John Hancock                                                                                                                                                                                                                                                   1212315       F2020063020200630000000
      "
    `);
  });

  it("Should generate a valid employee line", async function () {
    const contents = await extract(
      claims,
      transformDOREmployeesWageLines(employers, filingPeriods)
    );
    expect(contents).toMatchInlineSnapshot(`
      "B0000120200630Dave                                                                                                                                                                                                                                                           Smith                                                                                                                                                                                                                                                          000000000FT             1500.00             1500.00                0.00                0.00                0.00                0.00
      "
    `);
  });
});
