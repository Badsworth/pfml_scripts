import Document from "../../src/models/Document";
import findDocumentsByType from "../../src/utils/findDocumentsByType";

describe("findDocumentsByType", () => {
  const documentsList = [
    new Document({ document_type: "identity" }),
    new Document({ document_type: "certification" }),
  ];
  describe("when no documents are found", () => {
    it("returns an empty array", () => {
      const documents = findDocumentsByType(documentsList, "testType");

      expect(documents).toEqual([]);
    });
  });

  describe("when the documents list has multiple matching documents", () => {
    it("returns an array with all of the matching documents", () => {
      const testDocs = [
        new Document({ document_type: "testType" }),
        new Document({ document_type: "testType" }),
      ];
      const documents = findDocumentsByType(
        [...documentsList, ...testDocs],
        "testType"
      );

      expect(documents).toHaveLength(2);
      expect(documents).toEqual(testDocs);
    });
  });

  describe("when the documents list is empty", () => {
    it("returns an empty array", () => {
      const documents = findDocumentsByType([], "testType");
      expect(documents).toEqual([]);
    });
  });

  it("returns matching documents even if casing of document_type is different", () => {
    const testDocs = [
      new Document({ document_type: "Test Type" }),
      new Document({ document_type: "test Type" }),
    ];
    const documents = findDocumentsByType(
      [...documentsList, ...testDocs],
      "test type"
    );

    expect(documents).toHaveLength(2);
    expect(documents).toEqual(testDocs);
  });
});
