import { ApplicationRequestBody, DocumentUploadRequest } from "../../api";
import fs from "fs";
import { PDFCheckBox, PDFDocument, PDFOptionList, PDFTextField } from "pdf-lib";
import path from "path";
import { v4 as uuid } from "uuid";
import { DocumentWithPromisedFile } from "./index";
import { Uint8ArrayWrapper } from "../FileWrapper";

export type DocumentType = DocumentUploadRequest["document_type"];
export type PDFFormData = { [k: string]: string | boolean };
type PromisedDocument = Promise<Uint8Array>;

interface DocumentGeneratorInterface<C extends Record<string, unknown>> {
  generate(claim: ApplicationRequestBody, config: C): PromisedDocument;
  generateDocumentRequestBody(
    claim: ApplicationRequestBody,
    config: C
  ): DocumentWithPromisedFile;
}

export abstract class AbstractDocumentGenerator<
  C extends Record<string, unknown>
> implements DocumentGeneratorInterface<C> {
  constructor(public documentType: DocumentType) {}
  abstract documentSource: string;
  async generate(claim: ApplicationRequestBody, config: C): PromisedDocument {
    const formData = this.getFormData(claim, config);
    return this.fillPDFBytes(this.documentSource, formData);
  }
  generateDocumentRequestBody(
    claim: ApplicationRequestBody,
    config: C
  ): DocumentWithPromisedFile {
    const name = `${uuid()}.pdf`;
    return {
      document_type: this.documentType,
      name,
      // Return a callback to generate the file. This is important when dealing with millions of claims, as it allows us
      // to trigger generation at save time.
      file: async () =>
        this.generate(claim, config).then(
          (data) => new Uint8ArrayWrapper(data, name)
        ),
    };
  }
  abstract getFormData(claim: ApplicationRequestBody, config: C): PDFFormData;

  protected path(filename: string): string {
    return path.join(`${__dirname}`, "..", "..", "..", "forms", filename);
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
  async fillPDFBytes(source: string, data: PDFFormData): Promise<Uint8Array> {
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
}
