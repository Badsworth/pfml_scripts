import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";

/**
 * This is a stub for caring leave form, to be added soon.
 */
export default class CaringCertification extends AbstractDocumentGenerator<
  Record<string, unknown>
> {
  get documentSource(): string {
    return this.path("cat-pic.pdf");
  }
  getFormData(): PDFFormData {
    return {};
  }
}
