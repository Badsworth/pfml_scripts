import { ApplicationRequestBody } from "@/api";
import { promisify } from "util";
import fs from "fs";
import { FillPDFTaskOptions } from "../../cypress/plugins";
import {
  PDFArray,
  PDFBool,
  PDFDict,
  PDFDocument,
  PDFHexString,
  PDFName,
  PDFString,
} from "pdf-lib";
import formatDate from "date-fns/format";

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
  const [dobYear, dobMonth, dobDay] = claim.date_of_birth.split("-");
  const data: { [k: string]: string } = {
    untitled1: `${claim.first_name} ${claim.last_name}`,
    untitled46: `${claim.first_name} ${claim.last_name}`,
    untitled47: `${claim.first_name} ${claim.last_name}`,
    untitled48: `${claim.first_name} ${claim.last_name}`,
    untitled50: `${claim.first_name} ${claim.last_name}`,
    untitled4: `${dobMonth}`,
    untitled5: `${dobDay}`,
    untitled6: `${invalidHCP ? "" : dobYear}`,
    untitled3: `${invalidHCP ? "" : claim.tax_identifier?.slice(7)}`,
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
    claim.leave_details?.continuous_leave_periods &&
    claim.leave_details?.continuous_leave_periods[0]
  ) {
    const leave_period = claim.leave_details?.continuous_leave_periods[0];
    if (leave_period.start_date) {
      const [lsyear, lsmonth, lsday] = leave_period.start_date.split("-");
      data["untitled21"] = lsmonth;
      data["untitled22"] = lsday;
      data["untitled23"] = lsyear;
    }
    if (leave_period.end_date) {
      const [leyear, lemonth, leday] = leave_period.end_date.split("-");
      data["untitled24"] = lemonth;
      data["untitled25"] = leday;
      data["untitled26"] = leyear;
    }
    // @todo: Weeks of leave.  Calculate based on diff between start and end.
    data["untitled31"] = "2";
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
  unproofed?: boolean
): Promise<void> {
  if (!claim.first_name || !claim.last_name || !claim.date_of_birth) {
    throw new Error("Unable to generate document due to missing properties");
  }
  const dob = formatDate(new Date(claim.date_of_birth), "MM/dd/yyyy");
  if (claim.mass_id) {
    return fillPDF(`${__dirname}/../../forms/license-MA.pdf`, target, {
      "Name first": claim.first_name,
      "Name last": claim.last_name,
      "Date birth": dob,
      "License number": unproofed ? "" : claim.mass_id,
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
  const bytes = await fill(doc, data).save();
  await writeFile(target, bytes);
}

function fill(doc: PDFDocument, data: PDFFormData): PDFDocument {
  const getForm = (): PDFDict => {
    const acroForm = doc.context.lookup(
      doc.catalog.get(PDFName.of("AcroForm"))
    ) as PDFDict;
    if (!acroForm) {
      throw new Error("Unable to detect AcroForm from PDF");
    }
    return acroForm;
  };
  const getFields = (): PDFDict[] => {
    const acroForm = getForm();
    const acroFields = acroForm.context.lookup(
      acroForm.get(PDFName.of("Fields")),
      PDFArray
    );
    if (!acroFields) {
      return [];
    }
    return acroFields.asArray().map((ref) => {
      const field = acroForm.context.lookup(ref, PDFDict);
      if (!field) {
        throw new Error(`Unknown field by ref: ${ref}`);
      }
      return field;
    });
  };
  const extractFieldName = (field: PDFDict): string => {
    const fieldName = field.get(PDFName.of("T"));
    if (!fieldName || !(fieldName instanceof PDFString)) {
      throw new Error("Unable to extract name from field.");
    }
    return fieldName.asString();
  };
  const getField = (name: string): PDFDict => {
    const fields = getFields();
    const field = fields.find((field) => extractFieldName(field) === name);
    if (!field) {
      const names = fields.map(extractFieldName);
      throw new Error(
        `Unable to determine field for ${name}. Found: ${names.join(", ")}`
      );
    }
    return field;
  };

  // Debug block for filling every fillable field with its own name.
  // const names = getFields().map(extractFieldName);
  // for (const name of names) {
  //   const field = getField(name);
  //   field.set(PDFName.of("V"), PDFHexString.fromText(name));
  //   field.delete(PDFName.of("AP"));
  // }

  for (const [k, v] of Object.entries(data)) {
    const field = getField(k);
    field.set(PDFName.of("V"), PDFHexString.fromText(v));
    // Delete any appearance override that might be in place for this field.
    field.delete(PDFName.of("AP"));
    // Set readonly flag. @todo: This appears to break select boxes right now.
    // field?.set(PDFName.of('Ff'), PDFNumber.of(
    //   1 << 0 // Read Only
    // ));
  }
  // Important - set the NeedAppearances flag so the PDF viewer provides
  // the styling.
  getForm().set(PDFName.of("NeedAppearances"), PDFBool.True);
  return doc;
}
