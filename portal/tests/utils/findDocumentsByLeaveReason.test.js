import Document, { DocumentType } from "../../src/models/Document";
import LeaveReason from "../../src/models/LeaveReason";
import findDocumentsByLeaveReason from "../../src/utils/findDocumentsByLeaveReason";

describe("findDocumentsByLeaveReason", () => {
  const documentsList = [
    new Document({
      document_type: DocumentType.certification[LeaveReason.medical],
    }),
    new Document({
      document_type: DocumentType.certification[LeaveReason.medical],
    }),
  ];

  it("returns an empty array when no documents are found", () => {
    const documents = findDocumentsByLeaveReason(
      documentsList,
      LeaveReason.bonding
    );
    expect(documents).toEqual([]);
  });

  it("returns an array with all of the matching documents when the leave reason matches the doc type", () => {
    const testDocs = [
      new Document({ document_type: DocumentType.identityVerification }),
      new Document({ document_type: DocumentType.identityVerification }),
    ];
    const documents = findDocumentsByLeaveReason(
      [...documentsList, ...testDocs],
      LeaveReason.medical
    );

    expect(documents).toHaveLength(2);
    expect(documents).toEqual(documentsList);
  });

  it("returns an empty array when the documents list is empty", () => {
    const documents = findDocumentsByLeaveReason([], LeaveReason.medical);
    expect(documents).toEqual([]);
  });
});
