import { ApplicationRequestBody } from "../api";
import fs from "fs";
import { PDFCheckBox, PDFDocument, PDFOptionList, PDFTextField } from "pdf-lib";
import { parseISO, format, differenceInWeeks } from "date-fns";
import faker from "faker";

type PDFFormData = { [k: string]: string | boolean };
type PromisedDocument = Promise<Uint8Array>;
interface DocumentGenerator {
  (claim: ApplicationRequestBody, options: Record<string, unknown>): Promise<
    Uint8Array
  >;
}

const generateMassID = (
  claim: ApplicationRequestBody,
  { invalid }: { invalid?: boolean } = {}
): PromisedDocument => {
  if (
    !claim.first_name ||
    !claim.last_name ||
    !claim.date_of_birth ||
    !claim.mass_id
  ) {
    throw new Error("Unable to generate document due to missing properties");
  }
  const dob = format(parseISO(claim.date_of_birth), "MM/dd/yyyy");
  return fillPDFBytes(`${__dirname}/../../forms/license-MA.pdf`, {
    "Name first": claim.first_name,
    "Name last": claim.last_name,
    "Date birth": dob,
    "License number": claim.mass_id,
    "Date issue": "01/01/2016",
    "Date expiration": invalid ? "01/01/2020" : "01/01/2028",
    "Address street": claim.mailing_address?.line_1 ?? "",
    "Address state": claim.mailing_address?.state ?? "",
    "Address city": claim.mailing_address?.city ?? "",
    "address ZIP": claim.mailing_address?.zip ?? "",
  });
};

const generateOOSID = (
  claim: ApplicationRequestBody,
  { invalid }: { invalid?: boolean } = {}
): PromisedDocument => {
  if (!claim.first_name || !claim.last_name || !claim.date_of_birth) {
    throw new Error("Unable to generate document due to missing properties");
  }
  const dob = format(parseISO(claim.date_of_birth), "MM/dd/yyyy");
  return fillPDFBytes(`${__dirname}/../../forms/license-CT.pdf`, {
    "Name first": claim.first_name,
    "Name last": claim.last_name,
    "Date birth": dob,
    "License number": "XXX",
    "Date issue": "01/01/2020",
    "Date expiration": invalid ? "01/01/2020" : "01/01/2028",
    "Address street": claim.mailing_address?.line_1 ?? "",
    "Address state": claim.mailing_address?.state ?? "",
    "Address city": claim.mailing_address?.city ?? "",
    "address ZIP": claim.mailing_address?.zip ?? "",
  });
};

/**
 * Generates an HCP form for upload to the API.
 *
 * @param claim
 * @param target
 * @param invalidHCP
 */
const generateHCP = (
  claim: ApplicationRequestBody,
  { invalid }: { invalid?: boolean } = {}
): PromisedDocument => {
  if (!claim.first_name || !claim.last_name || !claim.date_of_birth) {
    throw new Error("Unable to generate document due to missing properties");
  }
  // Note: To debug this PDF's fields, follow this: https://stackoverflow.com/a/38257183
  const dob = parseISO(claim.date_of_birth);
  const data: { [k: string]: string } = {
    untitled1: `${claim.first_name} ${claim.last_name}`,
    untitled46: `${claim.first_name} ${claim.last_name}`,
    untitled47: `${claim.first_name} ${claim.last_name}`,
    untitled48: `${claim.first_name} ${claim.last_name}`,
    untitled50: `${claim.first_name} ${claim.last_name}`,
    untitled4: format(dob, "MM"),
    untitled5: format(dob, "dd"),
    untitled6: invalid ? "" : format(dob, "yyyy"),
    untitled3: `${invalid ? "" : claim.tax_identifier?.slice(7)}`,
    // Checkbox 5 - "I am taking leave because of my own serious health condition"
    untitled51: "Yes",
    // Checkbox 12 - "Does the patient have a serious health condition that necessitates continuing care􏰗"
    untitled56: "Yes",
    // Checkbox 13 - "When did the condition begin􏰗"
    untitled59: "Yes",
    // Checkbox 14 - "Which of the following characteristics apply..."
    untitled60: "Yes",
    // Checkbox 15 - "Is the patient􏰑s serious health condition a pregnancy􏰖related issue"
    untitled65: "Yes",
    // Checkbox 16 - "Is this health condition a work􏰖related injury􏰗"
    untitled67: "Yes",
    // Checkbox 17 - "Is this health condition related to the patient􏰑s military service􏰗"
    untitled69: "Yes",
    // Checkbox 19 - Leave Type? Continuous
    untitled72: "Yes",
    // Checkbox 22 - What level of physical exertion - very heavy
    untitled79: "Yes",
    // Checkbox 23 - Is your medical opinion that...
    untitled80: "Yes",
    // Checkbox 24 - "During this time􏰐 are there any other potentially work􏰖related activities" - Yes
    untitled82: "Yes",
    // Text 25 - What to refrain from:
    untitled29: "All work",
    // Checkbox 26  - Continuous Leave? Yes
    untitled84: "Yes",
    // Checkbox 27 - Reduced leave? No
    untitled87: "Yes",
    // Checkbox 29 - Intermittent Leave? No
    untitled88: "Yes",
    // Practitioner data.
    untitled39: "Theodore Cure, MD",
    untitled40: "[assume license is valid]",
    untitled41: "General Medicine",
    untitled42: "[assume business is valid]",
    untitled44: "555-555-5555",
    untitled45: "example@example.com",
  };
  let start_date = new Date();
  let end_date = new Date();

  if (
    claim.leave_details?.continuous_leave_periods?.[0]?.start_date &&
    claim.leave_details?.continuous_leave_periods?.[0]?.end_date
  ) {
    start_date = parseISO(
      claim.leave_details.continuous_leave_periods[0].start_date
    );
    end_date = parseISO(
      claim.leave_details.continuous_leave_periods[0].end_date
    );
  } else if (
    claim.leave_details?.reduced_schedule_leave_periods?.[0]?.start_date &&
    claim.leave_details?.reduced_schedule_leave_periods?.[0]?.end_date
  ) {
    console.warn(
      "Reduced leave HCP is not available. HCP will always describe continuous leave claim."
    );
    start_date = parseISO(
      claim.leave_details.reduced_schedule_leave_periods[0].start_date
    );
    end_date = parseISO(
      claim.leave_details.reduced_schedule_leave_periods[0].end_date
    );
  } else if (
    claim.leave_details?.intermittent_leave_periods?.[0]?.start_date &&
    claim.leave_details?.intermittent_leave_periods?.[0]?.end_date
  ) {
    console.warn(
      "Intermittent leave HCP is not available. HCP will always describe continuous leave claim."
    );
    start_date = parseISO(
      claim.leave_details.intermittent_leave_periods[0].start_date
    );
    end_date = parseISO(
      claim.leave_details.intermittent_leave_periods[0].end_date
    );
  }

  data["untitled21"] = format(start_date, "MM");
  data["untitled22"] = format(start_date, "dd");
  data["untitled23"] = format(start_date, "yyyy");
  data["untitled24"] = format(end_date, "MM");
  data["untitled25"] = format(end_date, "dd");
  data["untitled26"] = format(end_date, "yyyy");

  data["untitled31"] = differenceInWeeks(end_date, start_date).toString();

  return fillPDFBytes(`${__dirname}/../../forms/hcp-real.pdf`, data);
};

const generateBirthCertificate = async (
  claim: ApplicationRequestBody,
  { invalid }: { invalid?: boolean } = {}
): PromisedDocument => {
  if (!claim.leave_details?.child_birth_date) {
    throw new Error(
      `No birth date was given. Unable to generate birth certificate.`
    );
  }
  if (!claim.first_name || !claim.last_name) {
    throw new Error("Claim is missing required properties");
  }
  const gender = faker.random.number(1);
  const race = faker.random.arrayElement([
    "White",
    "Asian",
    "Black or African American",
    "Hispanic or Latino",
  ]);
  const dob = format(
    parseISO(claim.leave_details.child_birth_date),
    "MM/dd/yyyy"
  );

  const employee = {
    first_name: claim.first_name,
    last_name: claim.last_name,
  };
  if (invalid) {
    employee.first_name = faker.name.firstName(gender);
    employee.last_name = faker.name.lastName(gender);
  }
  const employeeName = `${employee.first_name} ${employee.last_name}`;
  const spouseName = faker.name.findName(undefined, employee.last_name, 0);
  const childName = faker.name.findName(undefined, employee.last_name, gender);
  const data = {
    "Certificate Number": "123",
    "Record Number": "123",
    "Date of Birth": dob,
    "Name of Child": childName,
    Sex: gender === 0 ? "Male" : "Female",
    Race: race,
    "Name of Mother": employeeName,
    "Name of Father": spouseName,
    "Birthplace of Mother": faker.fake("{{address.city}}, {{address.state}}"),
    "Birthplace of Father": faker.fake("{{address.city}}, {{address.state}}"),
    "Place of Birth": faker.fake("{{address.city}}, {{address.state}}"),
    "Residence of Parents": faker.fake("{{address.city}}, {{address.state}}"),
    "Occupation of Parent": "Widget Maker",
    "Date of Record": dob,
    "Name of Informant": faker.fake("{{name.firstName}} {{name.lastName}}"),
    "Address of Informant": faker.fake("{{address.city}}, {{address.state}}"),
    "Witness Date": dob,
  };
  return fillPDFBytes(`${__dirname}/../../forms/birth-certificate.pdf`, data);
};

const generatePrebirthLetter = async (
  claim: ApplicationRequestBody,
  { birthDate }: { birthDate?: string } = {}
): PromisedDocument => {
  if (!claim.last_name || !claim.leave_details?.child_birth_date) {
    throw new Error(
      "Claim missing required properties to generate a pre-birth letter"
    );
  }
  const dob = birthDate
    ? parseISO(birthDate)
    : parseISO(claim.leave_details?.child_birth_date);
  const data = {
    Date: "01/01/2021",
    "Name of Doctor": "Theodore T. Cure",
    "Name of Practice": "Cure Cares",
    "Name of Child(ren)": `${faker.name.firstName()} ${claim.last_name}`,
    "Name of Parent(s)": `${claim.first_name} ${claim.last_name}`,
    "Due Date": format(dob, "MM/dd/yyyy"),
  };
  return fillPDFBytes(`${__dirname}/../../forms/pre-birth-letter.pdf`, data);
};

function reformat(date: string): string {
  return format(parseISO(date), "MM/dd/yyyy");
}

const generateFosterPlacementLetter = async (
  claim: ApplicationRequestBody,
  { invalid }: { invalid?: boolean } = {}
): PromisedDocument => {
  if (
    !claim.leave_details?.continuous_leave_periods?.[0].start_date ||
    !claim.leave_details?.continuous_leave_periods?.[0].end_date
  ) {
    throw new Error("Invalid leave period to generate foster placement letter");
  }
  if (!claim.leave_details?.child_placement_date) {
    throw new Error(
      `Unable to generate foster placement letter without child placement date`
    );
  }
  const data = {
    "Date Leave to Begin": reformat(
      claim.leave_details?.continuous_leave_periods[0].start_date
    ),
    "Date Leave to End": reformat(
      claim.leave_details?.continuous_leave_periods[0].end_date
    ),
    "Actual or Anticipated Date of Adoption / Placement": reformat(
      claim.leave_details?.child_placement_date
    ),
    "Date Signed": "01/01/2021",
    Fax: "555-555-5555",
    "Signature of Employee": `${claim.first_name} ${claim.last_name}`,
    "Signature of Official": faker.name.findName(),
    "Phone Number": "555-555-1212",
    "Employee Name": invalid
      ? faker.name.findName()
      : `${claim.first_name} ${claim.last_name}`,
    Adoption: false,
    "Foster Care Placement": true,
    "Professional / Agency Name and Address": "[assume valid]",
    "Supervisor / Responsible Administrator Name": faker.name.findName(),
    "Employer Name": "[assume this matches claim]",
    "Employer Title": "[assume this matches claim]",
    "Employee's Work Schedule": "[assume this matches claim]",
  };
  return fillPDFBytes(`${__dirname}/../../forms/foster-adopt-cert.pdf`, data);
};

const generateAdoptionCertificate = async (
  claim: ApplicationRequestBody,
  { invalid }: { invalid?: boolean } = {}
): PromisedDocument => {
  if (
    !claim.leave_details?.continuous_leave_periods?.[0].start_date ||
    !claim.leave_details?.continuous_leave_periods?.[0].end_date
  ) {
    throw new Error("Invalid leave period to generate foster placement letter");
  }
  if (!claim.leave_details?.child_placement_date) {
    throw new Error(
      `Unable to generate foster placement letter without child placement date`
    );
  }
  const data = {
    "Date Leave to Begin": reformat(
      claim.leave_details?.continuous_leave_periods[0].start_date
    ),
    "Date Leave to End": reformat(
      claim.leave_details?.continuous_leave_periods[0].end_date
    ),
    "Actual or Anticipated Date of Adoption / Placement": reformat(
      claim.leave_details?.child_placement_date
    ),
    "Date Signed": "01/01/2021",
    Fax: "555-555-5555",
    "Signature of Employee": `${claim.first_name} ${claim.last_name}`,
    "Signature of Official": faker.name.findName(),
    "Phone Number": "555-555-1212",
    "Employee Name": invalid
      ? faker.name.findName()
      : `${claim.first_name} ${claim.last_name}`,
    Adoption: true,
    "Foster Care Placement": false,
    "Professional / Agency Name and Address": "[assume valid]",
    "Supervisor / Responsible Administrator Name": faker.name.findName(),
    "Employer Name": "[assume this matches claim]",
    "Employer Title": "[assume this matches claim]",
    "Employee's Work Schedule": "[assume this matches claim]",
  };
  return fillPDFBytes(`${__dirname}/../../forms/foster-adopt-cert.pdf`, data);
};

const generatePersonalLetter = async (
  claim: ApplicationRequestBody,
  { birthDate }: { birthDate?: string } = {}
): PromisedDocument => {
  if (!claim.leave_details?.child_birth_date) {
    throw new Error(
      "Claim missing required properties to generate a pre-birth letter"
    );
  }
  const dob = birthDate
    ? parseISO(birthDate)
    : parseISO(claim.leave_details?.child_birth_date);
  const data = {
    Date: "01/01/2021",
    "Name of Signee": "Robert Uncleman",
    Relationship: "Uncle",
    "Name of Parent(s)": `${claim.first_name} ${claim.last_name}`,
    "Due Date": format(dob, "MM/dd/yyyy"),
  };
  return fillPDFBytes(`${__dirname}/../../forms/personal-letter.pdf`, data);
};
const generateCatPicture: DocumentGenerator = async () => {
  const data = {};
  return fillPDFBytes(`${__dirname}/../../forms/cat-pic.pdf`, data);
};

const generators = {
  MASSID: generateMassID,
  OOSID: generateOOSID,
  HCP: generateHCP,
  BIRTHCERTIFICATE: generateBirthCertificate,
  PREBIRTH: generatePrebirthLetter,
  FOSTERPLACEMENT: generateFosterPlacementLetter,
  ADOPTIONCERT: generateAdoptionCertificate,
  PERSONALLETTER: generatePersonalLetter,
  CATPIC: generateCatPicture,
};

export default generators;

export type DocumentTypes = keyof typeof generators;

/**
 * Fills a PDF form using the pdf-lib module.
 *
 * We selected this module for its lack of external dependencies. It's kind of a pain
 * to work with, though.
 *
 * @param source
 * @param data
 */
async function fillPDFBytes(
  source: string,
  data: PDFFormData
): Promise<Uint8Array> {
  const buf = await fs.promises.readFile(source);
  const doc = await PDFDocument.load(Uint8Array.from(buf));

  // Fill in the PDF form.
  const form = doc.getForm();
  for (const [fieldName, fieldValue] of Object.entries(data)) {
    const field = form.getField(fieldName);
    if (field instanceof PDFTextField) {
      field.setText(fieldValue as string);
    } else if (field instanceof PDFCheckBox) {
      if (fieldValue) field.check();
      else field.uncheck();
    } else if (field instanceof PDFOptionList) {
      field.select(fieldValue as string);
    } else {
      throw new Error(`Unknown field type for ${fieldName}`);
    }
    // Necessary for checkboxes to show in Acrobat.
    field.enableReadOnly();
  }

  return doc.save();
}
