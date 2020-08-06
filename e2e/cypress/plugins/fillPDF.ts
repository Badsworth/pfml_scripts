import path from "path";
import fs from "fs";
import { promisify } from "util";
import {
  PDFArray,
  PDFDict,
  PDFDocument,
  PDFName,
  PDFBool,
  PDFHexString,
  PDFString,
} from "pdf-lib";
import type { FillPDFTaskOptions } from "./index";

const readFile = promisify(fs.readFile);
type PDFFormData = FillPDFTaskOptions["data"];

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
  data: PDFFormData
): Promise<string> {
  const buf = await readFile(path.resolve("cypress", "fixtures", source));
  const doc = await PDFDocument.load(buf);
  const bytes = await fill(doc, data).save();
  const out = Buffer.from(bytes.buffer);
  return out.toString("binary");
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
