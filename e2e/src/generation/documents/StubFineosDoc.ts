import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";

export default class StubFineosDoc extends AbstractDocumentGenerator<
  Record<string, unknown>
> {
  documentSource(): string {
    return this.path("cat-pic.pdf");
  }
  getFormData(): PDFFormData {
    return {};
  }
}
