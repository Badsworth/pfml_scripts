import fs from "fs";
import os from "os";
import path from "path";
import { PDFCheckBox, PDFDocument, PDFRadioGroup, PDFTextField } from "pdf-lib";
import { beforeAll, afterAll, describe, it, expect } from "@jest/globals";
import generateDocuments, {
  DocumentGenerationSpec,
  DocumentWithPromisedFile,
} from "../../../src/generation/documents";
import { ApplicationRequestBody } from "../../../src/api";
import config from "../../../src/config";
import { collect } from "streaming-iterables";

describe("Documents", function () {
  let tempDir: string;
  const hasServicePack = config("HAS_FINEOS_SP") === "true";

  beforeAll(async () => {
    tempDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "documents"));
  });

  afterAll(async () => {
    if (tempDir) {
      await fs.promises.rmdir(tempDir);
    }
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
    has_continuous_leave_periods: true,
    leave_details: {
      child_birth_date: "2020-08-01",
      child_placement_date: "2020-08-05",
      continuous_leave_periods: [
        {
          start_date: "2020-08-01",
          end_date: "2020-09-01",
        },
      ],
      caring_leave_metadata: {
        family_member_first_name: "Clarence",
        family_member_last_name: "Ellis",
        family_member_date_of_birth: "1943-05-11",
      },
    },
  };
  const intermittentAdditions: Partial<ApplicationRequestBody> = {
    has_continuous_leave_periods: false,
    has_intermittent_leave_periods: true,
    leave_details: {
      intermittent_leave_periods: [
        {
          start_date: "2020-08-01",
          end_date: "2020-08-15",
          duration: 1,
          duration_basis: "Days",
          frequency: 1,
          frequency_interval: 1,
          frequency_interval_basis: "Weeks",
        },
      ],
      caring_leave_metadata: {
        family_member_first_name: "Kimberly",
        family_member_last_name: "Bryant",
        family_member_date_of_birth: "1967-01-14",
      },
    },
  };
  const reducedAdditions: Partial<ApplicationRequestBody> = {
    has_continuous_leave_periods: false,
    has_reduced_schedule_leave_periods: true,
    leave_details: {
      reduced_schedule_leave_periods: [
        {
          start_date: "2020-08-15",
          end_date: "2020-08-30",
          sunday_off_minutes: 0,
          monday_off_minutes: 4 * 60,
          tuesday_off_minutes: 0,
          wednesday_off_minutes: 4 * 60,
          thursday_off_minutes: 0,
          friday_off_minutes: 4 * 60,
          saturday_off_minutes: 0,
        },
      ],
      caring_leave_metadata: {
        family_member_first_name: "Katherine",
        family_member_last_name: "Johnson",
        family_member_date_of_birth: "1918-08-26",
      },
    },
  };

  type FormValues = { [k: string]: string | boolean | undefined };
  async function parsePDF(
    document: DocumentWithPromisedFile
  ): Promise<FormValues> {
    const wrapper = await document.file();
    // Collect the stream parts and turn them into a UInt8Array we can parse.
    const parts = (await collect(wrapper.asStream())) as Buffer[];
    const doc = await PDFDocument.load(new Uint8Array(Buffer.concat(parts)));
    const values = await doc
      .getForm()
      .getFields()
      .reduce((values, field) => {
        if (field instanceof PDFTextField) {
          values[field.getName()] = field.getText();
        } else if (field instanceof PDFCheckBox) {
          values[field.getName()] = field.isChecked();
        } else if (field instanceof PDFRadioGroup) {
          values[field.getName()] = field.getSelected();
        } else {
          throw new Error("Cannot set values due to unknown field type");
        }
        return values;
      }, {} as { [k: string]: string | boolean | undefined });
    return values;
  }

  async function generate(
    claim: ApplicationRequestBody,
    options: DocumentGenerationSpec
  ): Promise<DocumentWithPromisedFile> {
    const documents = await generateDocuments(claim, options);
    const document = documents.pop();
    if (!document) {
      throw new Error("No document generated");
    }
    return document;
  }

  it("Should generate a Caring Leave Certification form", async function () {
    const document = await generate(claim, {
      CARING: {},
    });
    expect(document).toMatchObject({
      document_type: hasServicePack
        ? "Care for a family member form"
        : "State managed Paid Leave Confirmation",
    });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      /*
       * Assert Data Entered in
       * Section 1 - Employee Info
       */
      "Employee first name": "John",
      "Employee Last name": "Smith",
      "Emp. DOB mm": "06",
      "Emp. DOB dd": "07",
      "Emp. DOB yyyy": "2020",
      "Emp. SSI last 4": "0000",
      "Why are you applying for leave?":
        "To care for a family member with a serious health condition",

      /*
       * Assert Data Entered in
       * Section 2 - Family Member Info
       */
      "Family member name: First": "Clarence",
      "Family member name: Last": "Ellis",
      "Family member's date of birth: MM": "05",
      "Family member's date of birth: DD": "11",
      "Family member's date of birth: yyyy": "1943",
      "Family member address: Country:": "United States",
    });

    // Snapshot test to catch any unexpectedly changed values.
    expect(values).toMatchSnapshot({
      "Condition start mm": expect.any(String),
      "Condition start dd": expect.any(String),
      "Conditiion start yyyy": expect.any(String),
      "Employee signature date: MM": expect.any(String),
      "Employee signature date: DD": expect.any(String),
      "Employee signature date: yyyy": expect.any(String),
      "Family member address: Street:": expect.any(String),
      "Family member address: City:": expect.any(String),
      "Family member address: State:": expect.any(String),
      "Family member address: Zipcode:": expect.any(String),
    });
  });

  it("Should generate an invalid Caring Leave form", async function () {
    const document = await generate(claim, {
      CARING: { invalid: true },
    });
    const values = await parsePDF(document);
    // Assert DOB/SSN has correct values.
    expect(values).toMatchObject({
      "Emp. SSI last 4": undefined,
      "Emp. DOB mm": "06",
      "Emp. DOB dd": "07",
      "Emp. DOB yyyy": undefined,
    });
    expect(values).toMatchSnapshot({
      "Condition start mm": expect.any(String),
      "Condition start dd": expect.any(String),
      "Conditiion start yyyy": expect.any(String),
      "Employee signature date: MM": expect.any(String),
      "Employee signature date: DD": expect.any(String),
      "Employee signature date: yyyy": expect.any(String),
      "Family member address: Street:": expect.any(String),
      "Family member address: City:": expect.any(String),
      "Family member address: State:": expect.any(String),
      "Family member address: Zipcode:": expect.any(String),
    });
  });

  it("Should generate a valid Caring Leave form for a continuous leave claim", async function () {
    const document = await generate(claim, {
      CARING: {},
    });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Continuous leave": true,
      "Reduced leave schedule": false,
      "Intermittent leave": false,
      "Weeks of continuous leave": "4",
      // Assert Leave Dates
      "Continuous start dd": "01",
      "Continuous start mm": "08",
      "Continuous start yyyy": "2020",
      "Continuous end dd": "01",
      "Continuous end mm": "09",
      "Continuous end yyyy": "2020",
    });
  });

  it("Should generate a valid Caring Leave form for an intermittent leave claim", async function () {
    const document = await generate(
      { ...claim, ...intermittentAdditions },
      {
        CARING: {},
      }
    );
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Continuous leave": false,
      "Reduced leave schedule": false,
      "Intermittent leave": true,
      Absences: "Once per week",
      "Times per week": "1",
      Days: "1",
      // Assert leave dates Int
      "Intermittent start dd": "01",
      "Intermittent start mm": "08",
      "Intermittent start yyyy": "2020",
      "Intermittent end dd": "15",
      "Intermittent end mm": "08",
      "Intermittent end yyyy": "2020",
    });
  });

  it("Should generate a valid Caring Leave form for an reduced leave claim", async function () {
    const document = await generate(
      { ...claim, ...reducedAdditions },
      { CARING: {} }
    );
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Continuous leave": false,
      "Reduced leave schedule": true,
      "Intermittent leave": false,
      "Weeks of a reduced leave schedule": "2",
      "Hours of reduced leave schedule": "12",
      // Assert leave dates Int
      "Reduced start dd": "15",
      "Reduced start mm": "08",
      "Reduced start yyyy": "2020",
      "Reduced end dd": "30",
      "Reduced end mm": "08",
      "Reduced end yyyy": "2020",
    });
  });

  it("Should generate a HCP form", async function () {
    const document = await generate(claim, {
      HCP: {},
    });
    expect(document).toMatchObject({
      document_type: hasServicePack
        ? "Own serious health condition form"
        : "State managed Paid Leave Confirmation",
    });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      /*
       * Assert Data Entered in
       * Section 1 - Employee Info
       */
      "Employee first name": "John",
      "Employee Last name": "Smith",
      "Emp. DOB mm": "06",
      "Emp. DOB dd": "07",
      "Emp. DOB yyyy": "2020",
      "Emp. SSI last 4": "0000",
      "Are you applying for your own serious health condition?": "Yes",
    });

    // Snapshot test to catch any unexpectedly changed values.
    expect(values).toMatchSnapshot({
      "Condition start mm": expect.any(String),
      "Condition start dd": expect.any(String),
      "Conditiion start yyyy": expect.any(String),
    });
  });

  it("Should generate an invalid HCP form", async function () {
    const document = await generate(claim, {
      HCP: { invalid: true },
    });
    const values = await parsePDF(document);
    // Assert DOB/SSN has correct values.
    expect(values).toMatchObject({
      "Emp. SSI last 4": undefined,
      "Emp. DOB mm": "06",
      "Emp. DOB dd": "07",
      "Emp. DOB yyyy": undefined,
    });
    expect(values).toMatchSnapshot({
      "Condition start mm": expect.any(String),
      "Condition start dd": expect.any(String),
      "Conditiion start yyyy": expect.any(String),
    });
  });

  it("Should generate a valid HCP form for a continuous leave claim", async function () {
    const document = await generate(claim, {
      HCP: {},
    });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Continuous leave": true,
      "Reduced leave schedule": false,
      "Intermittent leave": false,
      "Weeks of continuous leave": "4",
      // Assert Leave Dates
      "Continuous start dd": "01",
      "Continuous start mm": "08",
      "Continuous start yyyy": "2020",
      "Continuous end dd": "01",
      "Continuous end mm": "09",
      "Continuous end yyyy": "2020",
    });
  });

  it("Should generate a valid HCP form for an intermittent leave claim", async function () {
    const document = await generate(
      { ...claim, ...intermittentAdditions },
      {
        HCP: {},
      }
    );
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Continuous leave": false,
      "Reduced leave schedule": false,
      "Intermittent leave": true,
      Absences: "Once per week",
      "Times per week": "1",
      Days: "1",
      // Assert leave dates Int
      "Intermittent start dd": "01",
      "Intermittent start mm": "08",
      "Intermittent start yyyy": "2020",
      "Intermittent end dd": "15",
      "Intermittent end mm": "08",
      "Intermittent end yyyy": "2020",
    });
  });

  it("Should generate a valid HCP form for an reduced leave claim", async function () {
    const document = await generate(
      { ...claim, ...reducedAdditions },
      { HCP: {} }
    );
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Continuous leave": false,
      "Reduced leave schedule": true,
      "Intermittent leave": false,
      "Weeks of a reduced leave schedule": "2",
      "Hours of reduced leave schedule": "12",
      // Assert leave dates Int
      "Reduced start dd": "15",
      "Reduced start mm": "08",
      "Reduced start yyyy": "2020",
      "Reduced end dd": "30",
      "Reduced end mm": "08",
      "Reduced end yyyy": "2020",
    });
  });

  it("Should generate an ID front", async function () {
    const document = await generate(claim, { MASSID: {} });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Address street": "123 Test Way",
      "Address state": "MA",
      "Address city": "Example",
      "address ZIP": "01000",
      "License number": "12345",
      "Name first": "John",
      "Name last": "Smith",
      "Date birth": "06/07/2020",
      "Date expiration": "01/01/2028",
    });
  });

  it("Should generate an invalid Mass ID", async function () {
    claim.mass_id = "123456789";
    const document = await generate(claim, { MASSID: { invalid: true } });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      "Date expiration": "01/01/2020",
    });
  });

  it("Should generate a non-mass ID", async function () {
    const document = await generate(claim, { OOSID: {} });
    const values = await parsePDF(document);
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
    await expect(values).toMatchSnapshot();
  });

  it("Should generate a birth certificate", async function () {
    const document = await generate(claim, { BIRTHCERTIFICATE: {} });
    const values = await parsePDF(document);
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
    const document = await generate(claim, {
      BIRTHCERTIFICATE: { invalid: true },
    });
    const values = await parsePDF(document);
    expect(values["Name of Mother"]).not.toEqual(
      `${claim.first_name} ${claim.last_name}`
    );
  });

  it("Should generate a pre-birth letter", async function () {
    const document = await generate(claim, { PREBIRTH: {} });
    const values = await parsePDF(document);
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
    const document = await generate(claim, { FOSTERPLACEMENT: {} });
    const values = await parsePDF(document);
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

  it("Should generate an invalid foster placement letter", async function () {
    const document = await generate(claim, {
      FOSTERPLACEMENT: { invalid: true },
    });
    const values = await parsePDF(document);
    expect(values["Employee Name"]).not.toEqual(
      `${claim.first_name} ${claim.last_name}`
    );
  });

  it("Should generate a adoption placement letter", async function () {
    const document = await generate(claim, { ADOPTIONCERT: {} });
    const values = await parsePDF(document);
    // const bytes = await generators.FOSTERPLACEMENT(claim, {});
    // const values = await parsePDF(bytes);
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
      Adoption: true,
      "Professional / Agency Name and Address": "[assume valid]",
      "Supervisor / Responsible Administrator Name": expect.any(String),
      "Employer Title": "[assume this matches claim]",
      "Employee's Work Schedule": "[assume this matches claim]",
      "Foster Care Placement": false,
    });
  });

  it("Should generate an invalid adoption placement letter", async function () {
    const document = await generate(claim, { ADOPTIONCERT: { invalid: true } });
    const values = await parsePDF(document);
    expect(values["Employee Name"]).not.toEqual(
      `${claim.first_name} ${claim.last_name}`
    );
  });

  it("Should generate a personal letter", async function () {
    const document = await generate(claim, { PERSONALLETTER: {} });
    const values = await parsePDF(document);
    expect(values).toMatchObject({
      Date: "01/01/2021",
      "Name of Signee": "Robert Uncleman",
      Relationship: "Uncle",
      "Name of Parent(s)": "John Smith",
      "Due Date": "08/01/2020",
    });
  });

  it("Should generate a cat picture", async function () {
    const document = await generate(claim, { CATPIC: {} });
    const values = await parsePDF(document);
    expect(values).toMatchObject({});
  });
});
