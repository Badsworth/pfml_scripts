import {
  AbstractDocumentGenerator,
  DocumentType,
  PDFFormData,
} from "./AbstractDocumentGenerator";

export default class CatPicture extends AbstractDocumentGenerator<
  Record<string, unknown>
> {
  get documentType(): DocumentType {
    return "State managed Paid Leave Confirmation";
  }
  get documentSource(): string {
    return this.path("cat-pic.pdf");
  }
  getFormData(): PDFFormData {
    return {};
  }
}
