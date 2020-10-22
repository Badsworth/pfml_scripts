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
      child_birth_date: "2020-08-01",
      child_placement_date: "2020-08-05",
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

  it("Should generate a birth certificate", async function () {
    const bytes = await generators.BIRTHCERTIFICATE(claim, {});
    const values = await parsePDF(bytes);
    expect(values).toMatchObject({
      "Certificate Number": expect.stringMatching(/\d+/),
      "Record Number": expect.stringMatching(/\d+/),
      "Date of Birth": expect.stringMatching(/\d{2}\/\d{2}\/\d{4}/),
      "Name of Child": expect.any(String),
      Sex: expect.stringMatching(/(M|F)/),
      Race: expect.any(String),
      "Name of Mother": expect.any(String),
      "Name of Father": expect.any(String),
      "Birthplace of Mother": expect.any(String),
      "Birthplace of Father": expect.any(String),
      "Place of Birth": expect.any(String),
      "Residence of Parents": expect.any(String),
      "Occupation of Parent": expect.any(String),
      "Date of Record": expect.stringMatching(/\d{2}\/\d{2}\/\d{4}/),
      "Name of Informant": expect.any(String),
      "Address of Informant": expect.any(String),
      "Witness Date": expect.stringMatching(/\d{2}\/\d{2}\/\d{4}/),
    });
  });

  it("Should generate a birth certificate with mismatched name", async function () {
    const bytes = await generators.BIRTHCERTIFICATE(claim, {
      mismatchedName: true,
    });
    const values = await parsePDF(bytes);
    expect(values["Name of Mother"]).not.toEqual(
      `${claim.first_name} ${claim.last_name}`
    );
  });

  it("Should generate a pre-birth letter", async function () {
    const bytes = await generators.PREBIRTH(claim, {});
    const values = await parsePDF(bytes);
    expect(values).toMatchObject({
      Date: "01/01/2021",
      "Name of Doctor": "Theodore T. Cure",
      "Name of Practice": "Cure Cares",
      "Name of Child(ren)": expect.stringMatching(/^\S+ Smith$/),
      "Name of Parent(s)": "John Smith",
      "Due Date": "08/01/2020",
    });
  });

  it("Should generate a foster placement letter", async function () {
    const bytes = await generators.FOSTERPLACEMENT(claim, {});
    const values = await parsePDF(bytes);
    await fs.promises.writeFile(`${__dirname}/../../pbl.pdf`, bytes);
    expect(values).toMatchObject({
      "Date Leave to Begin": "08/01/2020",
      "Actual or Anticipated Date of Adoption / Placement": "08/05/2020",
      "Date Leave to End": "09/01/2020",
      "Date Signed": "01/01/2021",
      Fax: "555-555-5555",
      "Signature of Employee": "John Smith",
      "Signature of Official": expect.any(String),
      "Phone Number": "555-555-1212",
      "Employer Name": "[assume this matches claim]",
      "Employee Name": "John Smith",
      Adoption: false,
      "Professional / Agency Name and Address": "[assume valid]",
      "Supervisor / Responsible Administrator Name": expect.any(String),
      "Employer Title": "[assume this matches claim]",
      "Employee's Work Schedule": "[assume this matches claim]",
      "Foster Care Placement": true,
    });
  });

  it("Should generate a adoption placement letter", async function () {
    const bytes = await generators.FOSTERPLACEMENT(claim, {});
    const values = await parsePDF(bytes);
    await fs.promises.writeFile(`${__dirname}/../../pbl.pdf`, bytes);
    expect(values).toMatchObject({
      "Date Leave to Begin": "08/01/2020",
      "Actual or Anticipated Date of Adoption / Placement": "08/05/2020",
      "Date Leave to End": "09/01/2020",
      "Date Signed": "01/01/2021",
      Fax: "555-555-5555",
      "Signature of Employee": "John Smith",
      "Signature of Official": expect.any(String),
      "Phone Number": "555-555-1212",
      "Employer Name": "[assume this matches claim]",
      "Employee Name": "John Smith",
      Adoption: false,
      "Professional / Agency Name and Address": "[assume valid]",
      "Supervisor / Responsible Administrator Name": expect.any(String),
      "Employer Title": "[assume this matches claim]",
      "Employee's Work Schedule": "[assume this matches claim]",
      "Foster Care Placement": true,
    });
  });

  it("Should generate a personal letter", async function () {
    const bytes = await generators.PERSONALLETTER(claim, {});
    const values = await parsePDF(bytes);
    expect(values).toMatchObject({
      Date: "01/01/2021",
      "Name of Signee": "Robert Uncleman",
      Relationship: "Uncle",
      "Name of Parent(s)": "John Smith",
      "Due Date": "08/01/2020",
    });
  });

  it("Should generate a cat picture", async function () {
    const bytes = await generators.CATPIC(claim, {});
    const values = await parsePDF(bytes);
    await fs.promises.writeFile(`${__dirname}/../../forms/cat-pic.pdf`, bytes);
    expect(values).toMatchObject({});
  });
});
