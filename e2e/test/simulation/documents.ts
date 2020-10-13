import fs from "fs";
import os from "os";
import path from "path";
import { PDFCheckBox, PDFDocument, PDFTextField } from "pdf-lib";
import { beforeAll, afterAll, describe, it, expect } from "@jest/globals";
import generators from "../../src/simulation/documents";
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
    tax_identifier: "000-00-0000",
    has_state_id: true,
    mass_id: "12345",
    mailing_address: {
      line_1: "123 Test Way",
      city: "Example",
      state: "MA",
      zip: "01000",
    },
    leave_details: {
      continuous_leave_periods: [
        {
          start_date: "2020-08-01",
          end_date: "2020-09-01",
        },
      ],
    },
  };

  type FormValues = { [k: string]: string | boolean | undefined };
  async function parsePDF(bytes: Uint8Array): Promise<FormValues> {
    const doc = await PDFDocument.load(bytes);
    const values = await doc
      .getForm()
      .getFields()
      .reduce((values, field) => {
        if (field instanceof PDFTextField) {
          values[field.getName()] = field.getText();
        } else if (field instanceof PDFCheckBox) {
          values[field.getName()] = field.isChecked();
        } else {
          throw new Error("Test");
        }
        return values;
      }, {} as { [k: string]: string | boolean | undefined });
    return values;
  }

  it("Should generate an HCP form", async function () {
    const bytes = await generators.HCP(claim, {});
    const values = await parsePDF(bytes);

    expect(values).toMatchObject({
      // Assert DOB has correct values.
      untitled4: "06", // DOB Month
      untitled5: "07", // DOB Day
      untitled6: "2020", // DOB Year.
      // Assert SSN has correct value
      untitled3: "0000",

      // Leave Start
      untitled21: "08", // Leave start month
      untitled22: "01", // Leave start day
      untitled23: "2020", // Leave start year
      // Leave End
      untitled24: "09", // Leave end month
      untitled25: "01", // Leave end day
      untitled26: "2020", // Leave end year
      // Weeks:
      untitled31: "4",
    });

    // Snapshot test to catch any unexpectedly changed values.
    expect(values).toMatchSnapshot();
  });

  it("Should generate an invalid HCP form", async function () {
    const bytes = await generators.HCP(claim, { invalid: true });
    const values = await parsePDF(bytes);
    // Assert DOB/SSN has correct values.
    expect(values).toMatchObject({
      untitled3: undefined,
      untitled4: "06", // DOB Month
      untitled5: "07", // DOB Day
      untitled6: undefined, // DOB Year.
    });
    expect(values).toMatchSnapshot();
  });

  it("Should generate an ID front", async function () {
    const bytes = await generators.MASSID(claim, {});
    const values = await parsePDF(bytes);
    expect(values).toMatchObject({
      "Address street": "123 Test Way",
      "Address state": "MA",
      "Address city": "Example",
      "address ZIP": "01000",
      "License number": "12345",
      "Name first": "John",
      "Name last": "Smith",
      "Date birth": "06/07/2020",
    });
    await expect(parsePDF(bytes)).resolves.toMatchSnapshot();
  });

  it("Should generate an ID front without MA ID number", async function () {
    claim.mass_id = "123456789";
    const bytes = await generators.MASSID(claim, { invalid: true });
    const values = await parsePDF(bytes);
    expect(values).toMatchObject({
      "Address street": "123 Test Way",
      "Address state": "MA",
      "Address city": "Example",
      "address ZIP": "01000",
      "License number": undefined,
      "Name first": "John",
      "Name last": "Smith",
      "Date birth": "06/07/2020",
    });
  });

  it("Should generate a non-mass ID", async function () {
    const bytes = await generators.OOSID(claim, {});
    const values = await parsePDF(bytes);
    expect(values).toMatchObject({
      "Address street": "123 Test Way",
      "Address state": "MA",
      "Address city": "Example",
      "address ZIP": "01000",
      "License number": "XXX",
      "Name first": "John",
      "Name last": "Smith",
      "Date birth": "06/07/2020",
    });
    await expect(parsePDF(bytes)).resolves.toMatchSnapshot();
  });
});
