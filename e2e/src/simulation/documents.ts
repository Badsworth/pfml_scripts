import { ApplicationRequestBody } from "@/api";
import { promisify } from "util";
import fs from "fs";
import { FillPDFTaskOptions } from "../../cypress/plugins";
import { PDFCheckBox, PDFDocument, PDFOptionList, PDFTextField } from "pdf-lib";
import { parseISO, format, differenceInWeeks } from "date-fns";

const readFile = promisify(fs.readFile);
const writeFile = promisify(fs.writeFile);

type PDFFormData = FillPDFTaskOptions["data"];

/**
 * Generates an HCP form for upload to the API.
 *
 * @param claim
 * @param target
 * @param invalidHCP
 */
export function generateHCP(
  claim: ApplicationRequestBody,
  target: string,
  invalidHCP = false
): Promise<void> {
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
    untitled6: invalidHCP ? "" : format(dob, "yyyy"),
    untitled3: `${invalidHCP ? "" : claim.tax_identifier?.slice(7)}`,
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

  if (
    claim.leave_details?.continuous_leave_periods?.[0].start_date &&
    claim.leave_details?.continuous_leave_periods?.[0].end_date
  ) {
    const start_date = parseISO(
      claim.leave_details.continuous_leave_periods[0].start_date
    );
    const end_date = parseISO(
      claim.leave_details.continuous_leave_periods[0].end_date
    );
    data["untitled21"] = format(start_date, "MM");
    data["untitled22"] = format(start_date, "dd");
    data["untitled23"] = format(start_date, "yyyy");

    data["untitled24"] = format(end_date, "MM");
    data["untitled25"] = format(end_date, "dd");
    data["untitled26"] = format(end_date, "yyyy");

    data["untitled31"] = differenceInWeeks(end_date, start_date).toString();
  }

  return fillPDF(`${__dirname}/../../forms/hcp-real.pdf`, target, data);
}

/**
 * Generates the front side of an ID, for upload to the API.
 *
 * @param claim
 * @param target
 * @param unproofed
 */
export function generateIDFront(
  claim: ApplicationRequestBody,
  target: string,
  invalid?: boolean
): Promise<void> {
  if (!claim.first_name || !claim.last_name || !claim.date_of_birth) {
    throw new Error("Unable to generate document due to missing properties");
  }
  const dob = format(parseISO(claim.date_of_birth), "MM/dd/yyyy");
  if (claim.mass_id) {
    return fillPDF(`${__dirname}/../../forms/license-MA.pdf`, target, {
      "Name first": claim.first_name,
      "Name last": claim.last_name,
      "Date birth": dob,
      "License number": invalid ? "" : claim.mass_id,
      "Date issue": "01/01/2020",
      "Date expiration": "01/01/2028",
      "Address street": claim.mailing_address?.line_1 ?? "",
      "Address state": claim.mailing_address?.state ?? "",
      "Address city": claim.mailing_address?.city ?? "",
      "address ZIP": claim.mailing_address?.zip ?? "",
    });
  } else {
    // @todo: Replace with OOS license when we have it.
    return fillPDF(`${__dirname}/../../forms/license-CT.pdf`, target, {
      "Name first": claim.first_name,
      "Name last": claim.last_name,
      "Date birth": dob,
      "License number": "XXX",
      "Date issue": "01/01/2020",
      "Date expiration": "01/01/2028",
      "Address street": claim.mailing_address?.line_1 ?? "",
      "Address state": claim.mailing_address?.state ?? "",
      "Address city": claim.mailing_address?.city ?? "",
      "address ZIP": claim.mailing_address?.zip ?? "",
    });
  }
}

/**
 * Generates the back side of an ID, for upload to the API.
 *
 * @param claim
 * @param target
 */
export async function generateIDBack(
  claim: ApplicationRequestBody,
  target: string
): Promise<void> {
  if (!claim.first_name || !claim.last_name) {
    throw new Error("Unable to generate document due to missing properties");
  }
  const contents = await readFile(`${__dirname}/../../forms/license-back.pdf`);
  return writeFile(target, contents);
}

/**
 * Fills a PDF form using the pdf-lib module.
 *
 * We selected this module for its lack of external dependencies. It's kind of a pain
 * to work with, though.
 *
 * @param source
 * @param data
 */
export default async function fillPDF(
  source: string,
  target: string,
  data: PDFFormData
): Promise<void> {
  const buf = await readFile(source);
  const doc = await PDFDocument.load(Uint8Array.from(buf));
  const bytes = await fill(doc, data).then((doc) => doc.save());
  await writeFile(target, bytes);
}

async function fill(doc: PDFDocument, data: PDFFormData): Promise<PDFDocument> {
  const form = doc.getForm();

  for (const [fieldName, fieldValue] of Object.entries(data)) {
    const field = form.getField(fieldName);
    if (field instanceof PDFTextField) {
      field.setText(fieldValue);
    } else if (field instanceof PDFCheckBox) {
      if (fieldValue) field.check();
      else field.uncheck();
    } else if (field instanceof PDFOptionList) {
      field.select(fieldValue);
    } else {
      throw new Error(`Unknown field type for ${fieldName}`);
    }
    // Necessary for checkboxes to show in Acrobat.
    field.enableReadOnly();
  }

  return doc;
}
