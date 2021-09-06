import Document, { DocumentType } from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import LeaveReason from "../../src/models/LeaveReason";

describe("DocumentCollection", () => {
  describe("#filterByApplication", () => {
    it("returns only Documents associated with the given application", () => {
      const applicationADocument1 = new Document({
        application_id: "a",
        fineos_document_id: "a_1",
      });
      const applicationADocument2 = new Document({
        application_id: "a",
        fineos_document_id: "a_2",
      });
      const applicationBDocument1 = new Document({
        application_id: "b",
        fineos_document_id: "b_1",
      });

      const collection = new DocumentCollection([
        applicationADocument1,
        applicationADocument2,
        applicationBDocument1,
      ]);

      expect(collection.filterByApplication("a")).toEqual([
        applicationADocument1,
        applicationADocument2,
      ]);
      expect(collection.filterByApplication("b")).toEqual([
        applicationBDocument1,
      ]);
    });
  });

  describe("#legalNotices", () => {
    it("returns only approvals, denials and requests for more info", () => {
      const legalNoticeTypes = new Set([
        DocumentType.approvalNotice,
        DocumentType.denialNotice,
        DocumentType.requestForInfoNotice,
      ]);
      const manyDocumentTypes = [
        DocumentType.approvalNotice,
        DocumentType.certification.certificationForm,
        DocumentType.certification[LeaveReason.care],
        DocumentType.certification.medicalCertification,
        DocumentType.denialNotice,
        DocumentType.identityVerification,
        DocumentType.medicalCertification,
        DocumentType.requestForInfoNotice,
      ];
      const documents = manyDocumentTypes.map(
        (document_type) => new Document({ document_type })
      );
      const documentCollection = new DocumentCollection(documents);

      const legalNotices = documentCollection.legalNotices;

      expect(
        legalNotices.every((doc) => legalNoticeTypes.has(doc.document_type))
      ).toBe(true);
    });
  });
});
