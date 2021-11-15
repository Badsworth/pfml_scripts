import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";

export default class CatPicture extends AbstractDocumentGenerator<
  Record<string, unknown>
> {
  documentSource(): string {
    return this.path("cat-pic.pdf");
  }
  getFormData(): PDFFormData {
    return {};
  }
}
